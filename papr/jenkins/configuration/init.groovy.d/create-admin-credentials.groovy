/* This init script regenerates a new JJB API token and injects it into a
 * credential.
 */

import hudson.model.*
import jenkins.model.*
import jenkins.security.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.domains.*
import org.jenkinsci.plugins.plaincredentials.*
import org.jenkinsci.plugins.plaincredentials.impl.*

StringCredentials findJJBCreds() {
    def creds = CredentialsProvider.lookupCredentials(
        StringCredentials.class,
        Jenkins.instance,
        null,
        null)
    for (c in creds) {
        if (c.id.equals("jenkins-job-builder"))
            return c
    }
}

jjb_creds = findJJBCreds()
if (!jjb_creds) {
    println("Didn't find JJB credentials, exiting...")
    return
}

/* we just use the admin user for now; should create more restricted service
 * account */
String regenApiToken() {
    User u = User.get("admin")
    ApiTokenProperty t = u.getProperty(ApiTokenProperty.class)
    t.changeApiToken()
    return t.getApiToken()
}

def new_token = regenApiToken()

Credentials new_jjb_creds = (Credentials) new StringCredentialsImpl(
    CredentialsScope.GLOBAL,
    jjb_creds.id, /* crucially; we copy the ID here to make it a clean swap */
    jjb_creds.description,
    hudson.util.Secret.fromString(new_token))

store = SystemCredentialsProvider.instance.store
store.updateCredentials(Domain.global(), jjb_creds, new_jjb_creds)
println("Successfully refreshed JJB credentials!")
