package com.kbstoolbox.app.data.remote

import com.kbstoolbox.app.session.SessionManager
import okhttp3.Interceptor
import okhttp3.Response

class AuthInterceptor(private val sessionManager: SessionManager) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = sessionManager.getAccessToken()
        val request = if (token != null) {
            chain.request().newBuilder()
                .addHeader("Authorization", "Bearer $token")
                .build()
        } else {
            chain.request()
        }
        val response = chain.proceed(request)
        if (response.code == 401) {
            // The token is invalid/expired/revoked server-side — clear the
            // local session so the UI drops back to the login screen instead
            // of silently failing every subsequent request.
            sessionManager.clearSession()
        }
        return response
    }
}
