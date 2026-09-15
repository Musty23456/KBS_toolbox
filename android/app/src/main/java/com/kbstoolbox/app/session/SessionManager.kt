package com.kbstoolbox.app.session

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

/**
 * Stores the access token and minimal session info using
 * EncryptedSharedPreferences (AES-256 via the Android Keystore) rather than
 * plain SharedPreferences, since a lost/rooted field device should not leak
 * a usable API token.
 */
class SessionManager(context: Context) {

    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    private val prefs: SharedPreferences = EncryptedSharedPreferences.create(
        context,
        "kbs_toolbox_secure_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    private val _sessionState = MutableStateFlow(readSession())
    val sessionState: StateFlow<SessionState> get() = _sessionState

    fun saveSession(accessToken: String, userId: String, fullName: String, email: String, role: String) {
        prefs.edit()
            .putString(KEY_ACCESS_TOKEN, accessToken)
            .putString(KEY_USER_ID, userId)
            .putString(KEY_FULL_NAME, fullName)
            .putString(KEY_EMAIL, email)
            .putString(KEY_ROLE, role)
            .apply()
        _sessionState.value = readSession()
    }

    fun clearSession() {
        prefs.edit().clear().apply()
        _sessionState.value = readSession()
    }

    fun getAccessToken(): String? = prefs.getString(KEY_ACCESS_TOKEN, null)

    private fun readSession(): SessionState {
        val token = prefs.getString(KEY_ACCESS_TOKEN, null) ?: return SessionState.LoggedOut
        return SessionState.LoggedIn(
            userId = prefs.getString(KEY_USER_ID, "") ?: "",
            fullName = prefs.getString(KEY_FULL_NAME, "") ?: "",
            email = prefs.getString(KEY_EMAIL, "") ?: "",
            role = prefs.getString(KEY_ROLE, "ENUMERATOR") ?: "ENUMERATOR",
            accessToken = token
        )
    }

    companion object {
        private const val KEY_ACCESS_TOKEN = "access_token"
        private const val KEY_USER_ID = "user_id"
        private const val KEY_FULL_NAME = "full_name"
        private const val KEY_EMAIL = "email"
        private const val KEY_ROLE = "role"
    }
}

sealed class SessionState {
    data object LoggedOut : SessionState()
    data class LoggedIn(
        val userId: String,
        val fullName: String,
        val email: String,
        val role: String,
        val accessToken: String
    ) : SessionState()
}
