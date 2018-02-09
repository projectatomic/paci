/* This init script injects the real GitHub token mounted into the container
 * into the stored credentials.
 */

import jenkins.model.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.domains.*
import org.jenkinsci.plugins.plaincredentials.*
import org.jenkinsci.plugins.plaincredentials.impl.*

StringCredentials findGitHubTokenCreds() {
    def creds = CredentialsProvider.lookupCredentials(
        StringCredentials.class,
        Jenkins.instance,
        null,
        null)
    for (c in creds) {
        if (c.description.equals("GitHub token"))
            return c
    }
}

github_creds = findGitHubTokenCreds()
if (!github_creds) {
    println("Didn't find GitHub token credentials, exiting...")
    return
}

def real_token_file = "/etc/github-token/token"
println("Reading token value from $real_token_file")
String real_token = new File(real_token_file).text.trim()

Credentials new_github_creds = (Credentials) new StringCredentialsImpl(
    CredentialsScope.GLOBAL,
    github_creds.id, /* crucially; we copy the ID here to make it a clean swap */
    github_creds.description,
    hudson.util.Secret.fromString(real_token))

store = SystemCredentialsProvider.instance.store
store.updateCredentials(Domain.global(), github_creds, new_github_creds)
println("Successfully updated credential token!")
