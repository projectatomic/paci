// This alleviates issues with long login on first try:
// https://github.com/openshift/jenkins/issues/501
// This fix was added upstream but then backed out because of:
// https://github.com/openshift/jenkins/issues/528
// We can remove this once it's included in the S2I image.
import jenkins.model.Jenkins
Jenkins.getInstance().getPluginManager().doCheckUpdatesServer()
Jenkins.getInstance().getUpdateCenter().getCoreSource().getData()
