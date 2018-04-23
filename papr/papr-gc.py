#!/usr/bin/python2

from __future__ import print_function

import json
import subprocess

# we want to do like OCP builds and keep e.g. the last 2 successful and the
# last 2 failed builds
KEEP_LAST_N = 2

out = subprocess.check_output(["oc", "get", "pods", "-o", "json",
                               "--sort-by", ".metadata.creationTimestamp"])
pods = json.loads(out)['items'] # sorted from oldest to newest

def delete_pods(pods, keep=-1):
    if keep != -1:
        if len(pods) <= keep:
            return
        pods = pods[:-keep]
    if len(pods) == 0:
        return
    names = [pod['metadata']['name'] for pod in pods]
    print("Deleting pods:", names)
    subprocess.check_call(["oc", "delete", "pods"] + names)

def delete_finished_pods(pods, keep=-1):
    failed = [pod for pod in pods if pod['status']['phase'] == 'Failed']
    delete_pods(failed, keep)
    succeeded = [pod for pod in pods if pod['status']['phase'] == 'Succeeded']
    delete_pods(succeeded, keep)

parent_label = 'papr.projectatomic.redhat.com/parent'
parents = [pod for pod in pods if pod['metadata']['labels'].get(parent_label) == 'true']
delete_finished_pods(parents, KEEP_LAST_N)

# this part will be redundant once we link their lifetimes more explicitly
child_label = 'papr.projectatomic.redhat.com/test-pod'
children = [pod for pod in pods if pod['metadata']['labels'].get(child_label) == 'true']
delete_finished_pods(children)
