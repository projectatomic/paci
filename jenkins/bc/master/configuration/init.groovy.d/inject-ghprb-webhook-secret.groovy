/* This init script injects the shared webhook secret generated from the
 * OCP template into the GHPRB authentication settings.
 *
 * Because GHPRB doesn't have a proper public API for this, we have to use some
 * introspection features. :(
 */

import java.lang.reflect.Field

import jenkins.model.*
import org.jenkinsci.plugins.ghprb.*

def secret_file = "/etc/webhook-secret/secret"
println("Reading webhook shared secret from $secret_file")
String secret = new File(secret_file).text.trim()

def descriptor = Jenkins.instance.getDescriptorByType(
        org.jenkinsci.plugins.ghprb.GhprbTrigger.DescriptorImpl.class)

def auth_list_field = descriptor.class.getDeclaredField("githubAuth")

/* needed to access private field */
auth_list_field.setAccessible(true)

def auth_list = (List<GhprbGitHubAuth>) auth_list_field.get(descriptor)

/* replace with an identical list with only the PAPR connection fixed (there
 * should only be one list there at all, but let's be safe) */
def new_auth_list = new ArrayList<GhprbGitHubAuth>(auth_list.size())

def modified = false
for (auth in auth_list) {

    if (!auth.description.equals("PAPR Connection")) {
        /* 👐 this is not the auth you're looking for */
        new_auth_list.add(auth)
        continue
    }

    new_auth_list.add(new GhprbGitHubAuth(
        auth.serverAPIUrl,
        auth.jenkinsUrl,
        auth.credentialsId,
        auth.description,
        auth.id,
        hudson.util.Secret.fromString(secret)))
    modified = true
}

if (modified) {
    auth_list_field.set(descriptor, new_auth_list)
    descriptor.save()
    println("Successfully injected GHPRB webhook secret!")
} else {
    println("Failed to find GHPRB PAPR auth!")
}
