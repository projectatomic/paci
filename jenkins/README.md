# PACI Jenkins

This directory defines the infrastructure for a Jenkins pipeline.

The infrastructure is instantiated by the `paci-jenkins.yaml` OpenShift template
which will create a Jenkins instance customized for PACI. This is heavily based
on the `jenkins-persistent` builtin OpenShift template, but with the following
enhancements:

- the GHPRB plugin is installed by default
- anonymous users have read access
- a GitHub token is securely installed at runtime using OpenShift secrets
- credentials for Jenkins Job Builder reconfiguration

The `jenkins/` directory is used by the S2I
[OpenShift Jenkins builder](https://github.com/openshift/jenkins/tree/8e58d88#installing-using-s2i-build)
to create the customized Jenkins master image.

The `slave/` directory is used by the `paci-jenkins-slave` buildconfig to create an
image for our Jenkins slave agent. This is used with the
[Kubernetes plugin](https://plugins.jenkins.io/kubernetes).

The `jjb/` directory contains job definitions. Jobs are created by the
`job-builder` buildconfig.

# Getting started

The OCP cluster used must be at least v3.6. If running `oc cluster up` locally,
it is highly recommended to exactly match the version of
[CentOS CI](https://console.apps.ci.centos.org:8443/console/), which is
currently v3.6.1. You can do this using the `--version=v3.6.1` switch. This will
ensure that you don't accidentally use features that will not be supported in
production.

## Setting up the Jenkins master

Assuming you already have a cluster set up and running (e.g. `oc cluster up`):

```
$ oc new-project projectatomic-ci
$ echo -n "$GITHUB_TOKEN" > mytoken
$ oc secrets new github-token token=mytoken
```

If you're also planning to test publishing results to AWS S3:

```
$ echo -n "$AWS_ACCESS_KEY_ID" > aws-key-id
$ echo -n "$AWS_SECRET_ACCESS_KEY" > aws-key-secret
$ oc secrets new aws-access-key id=aws-key-id secret=aws-key-secret
```

Now we can create the actual pipeline:

```
$ oc new-app --file paci-jenkins.yaml
```

If your project already exists (e.g. you are not a cluster admin) and it is not
named `projectatomic-ci`, make sure to pass the `-p NAMESPACE=$project` argument
to the `new-app` command above. (Though note that the `job-builder` Jenkinsfile
and `papr-trigger.py` script currently assume `projectatomic-ci` is the
namespace name, so for now those would require manual editing if different).

You can now start a build of the Jenkins image using:

```
$ oc start-build paci-jenkins
# to follow the build logs
$ oc logs --follow bc/paci-jenkins
```

Once the image is built, it will be automatically deployed and available at:

https://jenkins-projectatomic-ci.127.0.0.1.nip.io/

If you're working on your own fork, you can point OpenShift at it:

```
$ oc new-app --file paci-jenkins.yaml \
    -p REPO_URL=https://github.com/jlebon/projectatomic-ci-infra \
    -p REPO_REF=my-branch
```

This will change the source repos which are used for all the buildconfigs except
`papr`. Analogous `PAPR_REPO_URL` and `PAPR_REPO_REF` parameters exist for that.

Note that modifications to Jenkins configurations fed to the S2I builder will
probably require that you delete and recreate the PVC so that previous
configurations don't override new ones:


```
$ oc delete pvc jenkins
$ oc new-app ... # as above
<errors about existing objects, but recreates pvc>
# if modifications require a new Jenkins image
$ oc start-build paci-jenkins
# otherwise, to reuse the latest image built
$ oc rollout latest dc/jenkins
```

## Creating the Jenkins slave image

The next step is to create the container image that will be used for all
executions. To do this, simply do:

```
$ oc start-build paci-jenkins-slave
```

Modifications to the slave's `Dockerfile` will naturally require rebuilds of the
image in order for changes to take effect.

## Bootstrapping jobs

Rather than baking in the initial jobs into the image, jobs are created using
the `job-builder` buildconfig. To create the jobs, do:

```
$ oc start-build job-builder
```

Since this buildconfig uses the
[pipeline strategy](https://docs.openshift.com/container-platform/3.6/architecture/core_concepts/builds_and_image_streams.html#pipeline-build),
logs can be seen directly from Jenkins at:

https://jenkins-projectatomic-ci.127.0.0.1.nip.io/job/projectatomic-ci/job/projectatomic-ci-job-builder/

## Using webhooks locally

If you're comfortable using a closed-source service and app, Ultrahook is
[a popular way](https://blog.openshift.com/using-github-hooks-with-your-local-openshift-environment/)
to get webhooks working in your local OpenShift instance rather than exposing it
by poking holes in your firewall.

To get started, get an API key from
[the website](http://www.ultrahook.com/register), then `gem install ultrahook`,
then you can run e.g.:

```
# for branch pushes (event "Push")
$ ultrahook github https://jenkins-projectatomic-ci.127.0.0.1.nip.io/github-webhook/
# for PR (events "Issue comment", "Pull request")
$ ultrahook ghprb https://jenkins-projectatomic-ci.127.0.0.1.nip.io/ghprbhook/
```

⚠️ The trailing `/` is required! ⚠️

This will relay all hooks sent to `ghprb.$namespace.ultrahook.com` to GHPRB (and
`github...` to the GitHub plugin). You then simply need to use that same URL in
the webhook settings of GitHub repo of your choosing. Remember to use the same
shared secret as was generated/specified when you ran `new-app` (this can also
be obtained from the Web UI or from the CLI using
`oc extract secret/webhook-secret --to=-`).

If you would prefer not to set up webhooks, you'll need to add a `pollscm`
trigger as well as set `github-hooks` in `papr.yaml` to `false`.

## Hacking on PAPR

Note that hacking on the PAPR codebase *itself* doesn't require Jenkins, only a
working OpenShift cluster. See the PAPR
[instructions](https://github.com/projectatomic/papr/blob/ocp/docs/RUNNING.md)
for more details on how to get started.

The `papr` service account needs to have a membership in an SCC with `RunAsAny`,
so that it can run test containers as root, much like Docker. In the
`oc cluster up` case, this can be done simply by adding the papr service account
to the `anyuid` SCC. Otherwise, you'll need to ask a cluster administrator to do
this for you.

To be able to trigger PAPR tests from GHPRB jobs in Jenkins, you simply need to
build the PAPR image:

```
$ oc start-build papr
```

If you have your own development version of PAPR that you'd like the build to
use, you can specify a custom repo at `new-app`-time like this:

```
$ oc new-app --file paci-jenkins.yaml \
    -p PAPR_REPO_URL=https://github.com/jlebon/papr \
    -p PAPR_REPO_REF=ocp
```

(And of course, you can use `oc edit` to change the existing `papr` buildconfig
if it's already created.)

When GitHub webhooks are received, the GHPRB jobs trigger PAPR tests using the
`papr-trigger.py` script. Thus, if you're only looking to test PAPR running in a
pod (without e.g. having to `bot, retest this please` each time), you can
execute the `papr-trigger.py` script directly.
