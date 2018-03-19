#!/usr/bin/python2

'''
    This script is run by Jenkins papr-trigger-* jobs to convert GitHub events
    into a new PAPR pod. PAPR will then create a new collection of jobs for
    each testsuite to be tested.

    This can just as easily be run directly when hacking on PAPR. E.g.:

        ./papr-trigger.py --repo jlebon/papr-sandbox --branch tmp
'''

# Note we use Python 2 here because we run directly on the master to reduce
# overhead. TBD whether we want to add a new bc for creating custom base
# Jenkins S2I images with additional packages.

from __future__ import print_function

import os
import sys
import json
import uuid
import argparse
import tempfile
import subprocess


def main():

    args = parse_args()
    pod = generate_papr_pod(args)
    create_papr_pod(pod)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo', metavar='OWNER/REPO',
                         help="GitHub repo to test", required=True)
    parser.add_argument('--expected-sha1', metavar='SHA1',
                         help="Expected SHA1 of commit to test")
    parser.add_argument('--suites', metavar='CONTEXT1|CONTEXT2|...',
                         help="Pipe-separated list of testsuites to run")
    branch_or_pull = parser.add_mutually_exclusive_group(required=True)
    branch_or_pull.add_argument('--branch', help="GitHub branch to test",
                                default="")
    branch_or_pull.add_argument('--pull', metavar='ID', default="",
                                help="GitHub pull request ID to test")
    return parser.parse_args()


def generate_papr_pod(args):
    repo_name = args.repo[args.repo.index('/')+1:]
    target_name = args.branch if args.branch else args.pull
    uuid_name = uuid.uuid4().hex[:6] # XXX: actually check for collision
    pod_name = "papr-%s-%s-%s" % (repo_name, target_name, uuid_name)
    # XXX: Migrate to Jobs, which have nicer semantics. For now, we're stuck
    # with kube v1.6, which knows jobs, but doesn't support "backoffLimit".
    # https://github.com/kubernetes/kubernetes/issues/30243
    pod = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": pod_name,
            "labels": {
                "app": "papr"
            }
        },
        "spec": {
            "restartPolicy": "Never", # not a long-running svc, see XXX above
            "serviceAccountName": "papr",
            "containers": [
                {
                    "name": "papr",
                    "image": "172.30.1.1:5000/projectatomic-ci/papr",
                    "imagePullPolicy": "Always",
                    "args": ["--debug", "--repo", args.repo],
                    # XXX: pvc for git checkout caches
                    # XXX: mount site.yaml configmap
                    "volumeMounts": [
                        {
                            "name": "github-token-mount",
                            "mountPath": "/etc/github-token",
                            "readOnly": True
                        }
                    ]
                }
            ],
            "volumes": [
                {
                  "name": "github-token-mount",
                  "secret": {
                    # XXX: this is from the template; probably should just
                      # require the secret to have that exact name
                    "secretName": "github-token"
                  }
                }
            ]
        }
    }

    if args.branch:
        pod["spec"]["containers"][0]["args"].extend([
            "--branch", args.branch,
        ])
    else:
        pod["spec"]["containers"][0]["args"].extend([
            "--pull", args.pull,
        ])

    if args.expected_sha1:
        pod["spec"]["containers"][0]["args"].extend(
            ["--expected-sha1", args.expected_sha1]
        )

    if args.suites:
        for suite in args.suites.split('|'):
            pod["spec"]["containers"][0]["args"].extend(["--suite", suite])

    return pod


def create_papr_pod(pod):
    # store definition in an O_TMPFILE for passing to oc
    with tempfile.TemporaryFile() as tmpf:
        tmpf.write(json.dumps(pod).encode('utf-8'))
        tmpf.seek(0)
        subprocess.check_output(["oc", "create", "-f", "-"], stdin=tmpf)
    print(pod["metadata"]["name"])


if __name__ == '__main__':
    sys.exit(main())
