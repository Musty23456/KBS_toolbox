package com.kbstoolbox.app.data.repository

import com.kbstoolbox.app.data.remote.ApiService
import com.kbstoolbox.app.data.remote.dto.LoginRequestDto
import com.kbstoolbox.app.data.remote.dto.RegisterRequestDto
import com.kbstoolbox.app.session.SessionManager
import kotlinx.coroutines.flow.StateFlow

sealed class AuthResult {
    data object Success : AuthResult()
    data class Error(val message: String) : AuthResult()
}

class AuthRepository(
    private val apiService: ApiService,
    private val sessionManager: SessionManager
) {
    val sessionState: StateFlow<com.kbstoolbox.app.session.SessionState> = sessionManager.sessionState

    suspend fun login(email: String, password: String): AuthResult {
        return try {
            val loginResponse = apiService.login(LoginRequestDto(email, password))
            if (!loginResponse.isSuccessful || loginResponse.body() == null) {
                return AuthResult.Error(friendlyLoginError(loginResponse.code()))
            }
            val token = loginResponse.body()!!.access_token

            // Temporarily stash the token so the /me call below is
            // authenticated, then persist full session details once we know
            // who logged in.
            sessionManager.saveSession(token, userId = "", fullName = "", email = email, role = "ENUMERATOR")

            val meResponse = apiService.me()
            if (!meResponse.isSuccessful || meResponse.body() == null) {
                sessionManager.clearSession()
                return AuthResult.Error("Could not load your profile. Please try again.")
            }
            val user = meResponse.body()!!
            sessionManager.saveSession(token, user.id, user.full_name, user.email, user.role)
            AuthResult.Success
        } catch (e: Exception) {
            AuthResult.Error("No connection to the server. Check your network and try again.")
        }
    }

    suspend fun register(fullName: String, email: String, password: String): AuthResult {
        return try {
            val registerResponse = apiService.register(
                RegisterRequestDto(full_name = fullName, email = email, password = password)
            )
            if (!registerResponse.isSuccessful) {
                return AuthResult.Error(friendlyRegisterError(registerResponse.code()))
            }
            // Registration only creates the account; log the user straight in
            // afterwards so they land on the dashboard instead of a second
            // manual sign-in step.
            login(email, password)
        } catch (e: Exception) {
            AuthResult.Error("No connection to the server. Check your network and try again.")
        }
    }

    suspend fun logout() {
        try {
            apiService.logout()
        } catch (e: Exception) {
            // Best-effort: even if the server call fails (offline logout),
            // the local session is cleared below so the device still locks.
        } finally {
            sessionManager.clearSession()
        }
    }

    private fun friendlyLoginError(code: Int): String = when (code) {
        401 -> "Incorrect email or password."
        403 -> "This account has been disabled. Contact your administrator."
        else -> "Login failed (server returned $code). Please try again."
    }

    private fun friendlyRegisterError(code: Int): String = when (code) {
        409 -> "An account with this email already exists."
        422 -> "Check your details: name, a valid email, and a password of at least 8 characters."
        else -> "Registration failed (server returned $code). Please try again."
    }
}
