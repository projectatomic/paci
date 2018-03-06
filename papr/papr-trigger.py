#!/usr/bin/python2

'''
    This script is run by Jenkins papr-trigger-* jobs to convert GitHub events
    into a new PAPR pod. PAPR will then create a new collection of jobs for
    each testsuite to be tested.
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
    job = generate_papr_job(args)
    create_papr_job(job)

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


def generate_papr_job(args):
    repo_name = args.repo[args.repo.index('/')+1:]
    target_name = args.branch if args.branch else args.pull
    uuid_name = uuid.uuid4().hex[:6] # XXX: actually check for collision
    job_name = "papr-%s-%s-%s" % (repo_name, target_name, uuid_name)
    job = {
        "apiVersion": "batch/v1",
        "kind": "Job",
        "metadata": {
            "name": job_name,
            "labels": {
                "app": "papr"
            }
        },
        "spec": {
            "backoffLimit": 0,
            "template": {
                "spec": {
                    "restartPolicy": "Never",
                    "containers": [
                        {
                            "name": "papr",
                            # XXX: consider building this in PACI
                            "image": "docker.io/projectatomic/papr:latest",
                            # XXX: pvc for git checkout caches
                            "workingDir": "/tmp",
                            "env": [
                                {
                                    "name": "IN_OPENSHIFT",
                                    "value": "1"
                                },
                                {
                                    "name": "github_repo",
                                    "value": args.repo
                                },
                                {
                                    "name": "github_branch",
                                    "value": args.branch
                                },
                                {
                                    "name": "github_pull_id",
                                    "value": args.pull
                                },
                                {
                                    "name": "github_token",
                                    "valueFrom": {
                                        "secretKeyRef": {
                                            "name": "github-token",
                                            "key": "token"
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                }
            }
        }
    }

    if args.expected_sha1:
        job["spec"]["template"]["spec"]["containers"][0]["env"].append(
            {
                "name": "github_commit",
                "value": args.expected_sha1
            }
        )

    if args.suites:
        job["spec"]["template"]["spec"]["containers"][0]["env"].append(
            {
                "name": "github_contexts",
                "value": args.suites
            }
        )

    return job


def create_papr_job(job):
    # store definition in an O_TMPFILE for passing to oc
    with tempfile.TemporaryFile() as tmpf:
        tmpf.write(json.dumps(job).encode('utf-8'))
        tmpf.seek(0)
        subprocess.check_output(["oc", "create", "-f", "-"], stdin=tmpf)


if __name__ == '__main__':
    sys.exit(main())
