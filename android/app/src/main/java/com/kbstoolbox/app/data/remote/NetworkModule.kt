package com.kbstoolbox.app.data.remote

import com.kbstoolbox.app.BuildConfig
import com.kbstoolbox.app.session.SessionManager
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object NetworkModule {

    fun createApiService(sessionManager: SessionManager): ApiService {
        val loggingInterceptor = HttpLoggingInterceptor().apply {
            level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BODY else HttpLoggingInterceptor.Level.NONE
        }

        val client = OkHttpClient.Builder()
            .addInterceptor(AuthInterceptor(sessionManager))
            .addInterceptor(loggingInterceptor)
            // Render's free tier spins the backend down after inactivity and
            // can take 50+ seconds to wake back up on the first request, so
            // the previous 30s timeout was cutting that off mid-wake and
            // surfacing as "no connection" even though the server was fine.
            .connectTimeout(60, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(60, TimeUnit.SECONDS)
            .build()

        val baseUrl = BuildConfig.API_BASE_URL.let { if (it.endsWith("/")) it else "$it/" }

        val retrofit = Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(client)
            .addConverterFactory(GsonConverterFactory.create())
            .build()

        return retrofit.create(ApiService::class.java)
    }
}
