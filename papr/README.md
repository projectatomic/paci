# PAPR Jenkins

This directory defines the infrastructure for a PAPR pipeline.

The infrastructure is instantiated by the `papr-jenkins.yaml` OpenShift template
which will create a Jenkins instance customized for PAPR. This is heavily based
on the `jenkins-persistent` builtin OpenShift template, but with the following
enhancements:

- the GHPRB plugin is installed by default
- anonymous users have read access
- a GitHub token is securely installed at runtime using OpenShift secrets
- credentials for Jenkins Job Builder reconfiguration

The `jenkins/` directory is used by the S2I
[OpenShift Jenkins builder](https://github.com/openshift/jenkins/tree/8e58d88#installing-using-s2i-build)
to create the customized Jenkins master image.

The `slave/` directory is used by the `papr-slave` buildconfig to create an
image for our Jenkins slave agent. This is used with the
[Kubernetes plugin](https://plugins.jenkins.io/kubernetes).

The `jjb/` directory contains job definitions. Jobs are created by the
`job-builder` buildconfig.

# Getting started

## Setting up the Jenkins master

Assuming you already have a cluster set up and running (e.g. `oc cluster up`):

```
$ oc new-project papr
$ echo "$GITHUB_TOKEN" > mytoken
$ oc secrets new github-token token=mytoken
$ oc new-app --file papr-jenkins.yaml
```

If your project already exists (e.g. you are not a cluster admin) and it is not
named `papr`, make sure to pass the `-p NAMESPACE=$project` argument to the
`new-app` command above. (Though there may be spots that currently assume `papr`
is the namespace name).

You can now start a build of the PAPR Jenkins image using:

```
$ oc start-build papr-jenkins
# to follow the build logs
$ oc logs --follow bc/papr-slave
```

Once the image is built, it will be automatically deployed and available at:

https://jenkins-papr.127.0.0.1.nip.io/

If you're working on your own fork, you can point OpenShift at it:

```
$ oc new-app --file papr-jenkins.yaml \
    -p REPO_URL=https://github.com/jlebon/projectatomic-ci-infra \
    -p REPO_REF=my-branch
```

Note that modifications to Jenkins configurations fed to the S2I builder will
probably require that you delete and recreate the PVC so that previous
configurations don't override new ones:


```
$ oc delete pvc jenkins
$ oc new-app ... # as above
<errors about existing objects, but recreates pvc>
# if modifications require a new Jenkins image
$ oc start-build papr-jenkins
# otherwise, to reuse the latest image built
$ oc rollout latest dc/jenkins
```

## Creating the Jenkins slave image

The next step is to create the container image that will be used for all
executions. To do this, simply do:

```
$ oc start-build papr-slave
# to follow the build logs
$ oc logs --follow bc/papr-slave
```

Modifications to the slave's `Dockerfile` will naturally require rebuilds of the
image in order for changes to take effect.

## Bootstrapping jobs

Rather than baking in the initial jobs into the image, jobs are created using
the `job-builder` buildconfig. To create the jobs, do:

```
$ oc start-builder job-builder
```

Since this buildconfig uses the
[pipeline strategy](https://docs.openshift.com/container-platform/3.6/architecture/core_concepts/builds_and_image_streams.html#pipeline-build),
logs can be seen directly from Jenkins.

## Using webhooks locally

If you're comfortable using a closed-source service and app, Ultrahook is
[a popular way](https://blog.openshift.com/using-github-hooks-with-your-local-openshift-environment/)
to get webhooks working in your local OpenShift instance rather than exposing it
by poking holes in your firewall.

To get started, get an API key from
[the website](http://www.ultrahook.com/register), then `gem install ultrahook`,
then you can run e.g.:

```
$ ultrahook github https://jenkins-papr.127.0.0.1.nip.io/ghprbhook/
```

This will relay all hooks sent to `github.$namespace.ultrahook.com` to GHPRB.
You then simply need to use that same URL in the GitHub repo of your choosing.
Remember to use the same shared secret as was generated/specified when you ran
`new-app`.
