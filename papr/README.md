# PAPR Jenkins

This directory defines the infrastructure for a PAPR pipeline.

The infrastructure is instantiated by the `papr-jenkins.yaml` OpenShift template
which will create a Jenkins instance customized for PAPR. This is heavily based
on the `jenkins-persistent` builtin OpenShift template, but with the following
enhancements:

- the GHPRB plugin is installed by default
- anonymous users have read access
- a GitHub token is securely installed at runtime using OpenShift secrets

The `jenkins/` directory is used by the S2I
[OpenShift Jenkins builder](https://github.com/openshift/jenkins/tree/8e58d88#installing-using-s2i-build)
to create the customized Jenkins image.

# Usage

Assuming you already have a cluster set up and running (e.g. `oc cluster up`):

```
$ oc new-project papr
$ echo "$GITHUB_TOKEN" > mytoken
$ oc secrets new github-token token=mytoken
$ oc new-app --file papr-jenkins.yaml
```

If your project already exists (e.g. you are not a cluster admin) and it is not
named `papr`, make sure to pass the `-p NAMESPACE=$project` argument to the
`new-app` command above.

You can now start a build of the PAPR Jenkins image using:

```
$ oc start-build papr-jenkins
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
probably require that you delete and recreate the PVC so that old configurations
don't override new ones (I find it easier to just `oc delete project papr` and
recreate it; the builder image is cached in the `openshift` namespace).

# Using webhooks locally

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
