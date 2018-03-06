// XXX: extend openshift/jenkins S2I builder so we can easily bake custom cloud
// configs in config.xml.tpl so we don't need to `podTemplate` each time
podTemplate(label: 'paci-slave', cloud: 'openshift', containers: [
    // XXX: directly using the clusterIP is the only way I could get this to
    // work -- using 'docker-registry.default.svc.cluster.local' fails
    containerTemplate(name: 'jnlp', image: '172.30.1.1:5000/projectatomic-ci/paci-jenkins-slave',
                      args: '${computer.jnlpmac} ${computer.name}')
    ]) {

    node('paci-slave') {
        checkout scm
        withCredentials([string(credentialsId: 'jenkins-job-builder',
                                variable: 'PASSWD')]) {
            sh 'jenkins-jobs --conf jenkins/jjb/config -p $PASSWD update jenkins/jjb'
        }
    }
}
