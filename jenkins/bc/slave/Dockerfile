FROM openshift/jenkins-slave-base-centos7

# This image is used to run jenkins-jobs and PAPR itself.

# Let's use py3 since we can and 3 > 2.
RUN yum install -y epel-release && \
    yum install -y python34-pip && \
    yum clean all -y && \
    rm -rf /var/cache/yum && \
    pip3 install jenkins-job-builder

# we don't need root; we run as the `jenkins` user created
# in the base image.
USER 1001
