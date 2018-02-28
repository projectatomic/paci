FROM openshift/jenkins-slave-base-centos7

# This image is used to run jenkins-jobs and PAPR itself.

RUN yum install -y epel-release && \
    yum install -y python2-pip && \
    yum clean all -y && \
    rm -rf /var/cache/yum && \
    pip install jenkins-job-builder && \
    pip install -U six # seems like jjb declares 1.9.0 but needs 1.10.0

# we don't need root; we run as the `jenkins` user created
# in the base image.
USER 1001
