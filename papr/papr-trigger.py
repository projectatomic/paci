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
import argparse
import tempfile
import subprocess


# XXX: Need to figure out GC strategy for the pod we create here (the "child"
# pods that PAPR creates are cleaned up by PAPR itself -- once we set up owner
# references, then even aborted PAPR jobs should end up cleaning child pods
# when we GC the parent). Maybe a Jenkins job to do this? Would want similar
# semantics like successfulBuildsHistoryLimit and failedBuildsHistoryLimit.
# Also note we'll still need this even once we move to Kubernetes Jobs, though
# owner references are implicitly added for child pods.


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
    repo_owner, repo_name = args.repo.split('/')
    target_name = args.branch if args.branch else args.pull
    # XXX: Migrate to Jobs, which have nicer semantics. For now, we're stuck
    # with kube v1.6, which knows jobs, but doesn't support "backoffLimit".
    # https://github.com/kubernetes/kubernetes/issues/30243
    pod = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "generateName": "papr-%s-%s-" % (repo_name, target_name),
            "labels": {
                "app": "papr",
                "papr.projectatomic.redhat.com/parent": "true",
                "papr.projectatomic.redhat.com/github-repo-owner": repo_owner,
                "papr.projectatomic.redhat.com/github-repo-name": repo_name,
                "papr.projectatomic.redhat.com/github-target": target_name
            }
        },
        "spec": {
            "restartPolicy": "Never", # not a long-running svc, see XXX above
            "serviceAccountName": "papr",
            "containers": [
                {
                    "name": "papr",
                    # XXX: in `oc cluster up`, you need to directly use the
                    # registry clusterIP, e.g. 172.30.1.1:5000
                    "image": "docker-registry.default.svc:5000/projectatomic-ci/papr",
                    "imagePullPolicy": "Always",
                    "args": ["--debug", "runtest", "--conf",
                             "/etc/papr/config", "--repo", args.repo],
                    "securityContext": {
                        "runAsUser": 0
                    },
                    # XXX: pvc for git checkout caches (but need to add locking)
                    "env": [
                        {
                            "name": "GITHUB_TOKEN",
                            "valueFrom": {
                                "secretKeyRef": {
                                    "name": "github-token",
                                    "key": "token",
                                    "optional": False
                                }
                            }
                        },
                        {
                            "name": "AWS_ACCESS_KEY_ID",
                            "valueFrom": {
                                "secretKeyRef": {
                                    "name": "aws-access-key",
                                    "key": "id",
                                    "optional": False
                                }
                            }
                        },
                        {
                            "name": "AWS_SECRET_ACCESS_KEY",
                            "valueFrom": {
                                "secretKeyRef": {
                                    "name": "aws-access-key",
                                    "key": "secret",
                                    "optional": False
                                }
                            }
                        }
                    ],
                    "volumeMounts": [
                        {
                            "name": "config-mount",
                            "mountPath": "/etc/papr"
                        }
                    ]
                }
            ],
            "volumes": [
                {
                    "name": "config-mount",
                    "configMap": {
                        "name": "papr-config"
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
        subprocess.check_call(["oc", "create", "-f", "-"], stdin=tmpf)


if __name__ == '__main__':
    sys.exit(main())
