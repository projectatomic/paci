/* This init script injects the real GitHub webhook shared secret mounted into
 * the container into the stored credentials.
 */

import jenkins.model.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.domains.*
import org.jenkinsci.plugins.plaincredentials.*
import org.jenkinsci.plugins.plaincredentials.impl.*

StringCredentials findGitHubWebhookSharedSecretCreds() {
    def creds = CredentialsProvider.lookupCredentials(
        StringCredentials.class,
        Jenkins.instance,
        null,
        null)
    for (c in creds) {
        if (c.id.equals("github-webhook-shared-secret"))
            return c
    }
}

webhook_creds = findGitHubWebhookSharedSecretCreds()
if (!webhook_creds) {
    println("Didn't find GitHub webhook shared secret credentials, exiting...")
    return
}

def secret_file = "/etc/webhook-secret/secret"
println("Reading webhook shared secret from $secret_file")
String secret = new File(secret_file).text.trim()

Credentials new_webhook_creds = (Credentials) new StringCredentialsImpl(
    CredentialsScope.GLOBAL,
    webhook_creds.id, /* crucially; we copy the ID here to make it a clean swap */
    webhook_creds.description,
    hudson.util.Secret.fromString(secret))

store = SystemCredentialsProvider.instance.store
store.updateCredentials(Domain.global(), webhook_creds, new_webhook_creds)
println("Successfully updated GitHub webhook shared secret credentials!")
