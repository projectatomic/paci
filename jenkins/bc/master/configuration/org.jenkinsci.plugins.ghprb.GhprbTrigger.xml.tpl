<?xml version='1.0' encoding='UTF-8'?>
<org.jenkinsci.plugins.ghprb.GhprbTrigger_-DescriptorImpl plugin="ghprb@1.39.0">
  <configVersion>1</configVersion>
  <!-- make these the same as before -->
  <whitelistPhrase>(?m)^\s*bot,\s+add\s+author\s+to\s+whitelist\s*\.?$</whitelistPhrase>
  <okToTestPhrase>(?m)^\s*bot,\s+test\s+pull\s+request\s*\.?$</okToTestPhrase>
  <retestPhrase>(?m)^\s*bot,\s+test\s+pull\s+request\s+once\s*\.?$</retestPhrase>
  <skipBuildPhrase>.*\[skip\W+ci\].*</skipBuildPhrase>
  <blackListCommitAuthor></blackListCommitAuthor>
  <!-- note we exclusively use webhooks, so shouldn't actually need cron -->
  <cron>H/10 * * * *</cron>
  <useComments>false</useComments>
  <useDetailedComments>false</useDetailedComments>
  <manageWebhooks>false</manageWebhooks>
  <unstableAs>FAILURE</unstableAs>
  <autoCloseFailedPullRequests>false</autoCloseFailedPullRequests>
  <displayBuildErrorsOnDownstreamBuilds>false</displayBuildErrorsOnDownstreamBuilds>
  <blackListLabels></blackListLabels>
  <whiteListLabels></whiteListLabels>
  <githubAuth>
    <org.jenkinsci.plugins.ghprb.GhprbGitHubAuth>
      <serverAPIUrl>https://api.github.com</serverAPIUrl>
      <description>PAPR Connection</description>
      <credentialsId>github-token</credentialsId>
      <id>7a64217f-077c-4fde-a9a3-fd0ae37d4e0a</id>
      <!-- this will be replaced at startup by init.groovy -->
      <secret>SOOPERSEKRIT</secret>
    </org.jenkinsci.plugins.ghprb.GhprbGitHubAuth>
  </githubAuth>
  <adminlist></adminlist>
  <requestForTestingPhrase>Can one of the admins verify this patch?</requestForTestingPhrase>
  <extensions>
    <org.jenkinsci.plugins.ghprb.extensions.status.GhprbSimpleStatus>
      <commitStatusContext></commitStatusContext>
      <showMatrixStatus>false</showMatrixStatus>
      <addTestResults>false</addTestResults>
      <completedStatus/>
    </org.jenkinsci.plugins.ghprb.extensions.status.GhprbSimpleStatus>
  </extensions>
</org.jenkinsci.plugins.ghprb.GhprbTrigger_-DescriptorImpl>
