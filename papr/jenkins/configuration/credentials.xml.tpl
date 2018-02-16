<?xml version='1.0' encoding='UTF-8'?>
<com.cloudbees.plugins.credentials.SystemCredentialsProvider plugin="credentials@1.23">
  <domainCredentialsMap class="hudson.util.CopyOnWriteMap$Hash">
    ${KUBERNETES_CREDENTIALS}
    <entry>
      <com.cloudbees.plugins.credentials.domains.Domain>
        <specifications/>
      </com.cloudbees.plugins.credentials.domains.Domain>
      <java.util.concurrent.CopyOnWriteArrayList>
        <org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl plugin="plain-credentials@1.3">
          <scope>GLOBAL</scope>
          <description>GitHub token</description>
          <id>github-token</id>
          <!-- this will be replaced at startup by init.groovy -->
          <secret>SOOPERSEKRIT</secret>
        </org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>
        <org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl plugin="plain-credentials@1.3">
          <scope>GLOBAL</scope>
          <description>API token for JJB</description>
          <id>jenkins-job-builder</id>
          <!-- this will be replaced at startup by init.groovy -->
          <secret>SOOPERSEKRIT</secret>
        </org.jenkinsci.plugins.plaincredentials.impl.StringCredentialsImpl>
      </java.util.concurrent.CopyOnWriteArrayList>
    </entry>
  </domainCredentialsMap>
</com.cloudbees.plugins.credentials.SystemCredentialsProvider>
