function hash_password(username, password) {
	// We are not using a random salt here because it would significantly
	// increase complexity (and therefore attack surface) with very little
	// benefit. The backend already computes a second hash with a random salt
	// before storage, so this is no more dangerous in the event that the
	// database is compromised. The only problem would be if the hashed
	// password was intercepted in transit (perhaps the server is compromised).
	// This is not much of an issue since the salts here are guranteed to be
	// unique since they are derived from the username. This can be dangerous
	// as users often reuse usernames across websites, but this is why we also
	// incorperate "filmbrowser_username_salt". Thus, this hash's salt will be
	// unique, and the salt used before everything is stored is random, so there
	// really isn't any cause for concern, it just looks a little scary at first.
	
    return sodium.crypto_pwhash(
        32,//hashlen
        password,//pass
        sodium.crypto_generichash(
			16,
			username,
			"filmbrowser_username_salt"
		),//salt
        sodium.crypto_pwhash_OPSLIMIT_INTERACTIVE,//iterations
        sodium.crypto_pwhash_MEMLIMIT_INTERACTIVE,//memory
        sodium.crypto_pwhash_ALG_ARGON2ID13//argon2 mode
    );
}

function login() {
	var form = document.getElementById("loginform")
	var username = form.username.value
	var password = form.password.value
	password_hash = btoa(hash_password(username.toLowerCase(), password))
	login_with_hash(username, password_hash)
}

function login_with_hash(username, password_hash) {
	$("#loginform #errortext").hide()
	
	fail_func = (statusText) => {
		$("#loginform #errortext").text(statusText.responseText)
		$("#loginform #errortext").show()
	}
	success_func = () => {
		console.log("Logged in")
		window.location.replace("/")
	}
	$.ajax({
		type: "POST",
		url: "/auth/login",
		data: JSON.stringify({
			username: username,
			password: password_hash
		}),
		contentType: "application/jsonrequest; charset=utf-8",
		success: success_func,
		error: fail_func
	})
}

function register() {
	$("#registerform #errortext").hide()
	
	var form = document.getElementById("registerform")
	var username = form.username.value
	var password = form.password.value
	var confpassword = form.cpassword.value
	
	fail_func = (statusText) => {
		$("#registerform #errortext").text(statusText.responseText)
		$("#registerform #errortext").show()
	}
	success_func = () => {
		console.log("Registered, logging in")
		login_with_hash(username, password_hash)
	}
	
	if(password !== confpassword) {
		fail_func({responseText: "Passwords must match!"})
		return
	}
	
	var password_hash = btoa(hash_password(username.toLowerCase(), password))
	$.ajax({
		type: "POST",
		url: "/auth/register",
		data: JSON.stringify({
			username: username,
			password: password_hash
		}),
		contentType: "application/jsonrequest; charset=utf-8",
		success: success_func,
		error: fail_func
	})
}