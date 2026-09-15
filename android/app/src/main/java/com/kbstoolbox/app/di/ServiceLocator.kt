package com.kbstoolbox.app.di

import android.content.Context
import android.provider.Settings
import com.kbstoolbox.app.data.local.AppDatabase
import com.kbstoolbox.app.data.remote.ApiService
import com.kbstoolbox.app.data.remote.NetworkModule
import com.kbstoolbox.app.data.repository.AuthRepository
import com.kbstoolbox.app.data.repository.SubmissionRepository
import com.kbstoolbox.app.data.repository.SurveyRepository
import com.kbstoolbox.app.data.repository.SyncRepository
import com.kbstoolbox.app.session.SessionManager
import com.kbstoolbox.app.sync.NetworkConnectivityObserver

/**
 * Deliberately plain, hand-written dependency container instead of Hilt.
 * Hilt's KSP/annotation-processing setup is a common source of build
 * failures that only surface when actually compiled — since this project
 * cannot be compiled in the environment it was authored in, removing that
 * risk was judged more valuable than the boilerplate this class saves.
 */
object ServiceLocator {

    @Volatile private var sessionManager: SessionManager? = null
    @Volatile private var apiService: ApiService? = null
    @Volatile private var database: AppDatabase? = null
    @Volatile private var authRepository: AuthRepository? = null
    @Volatile private var surveyRepository: SurveyRepository? = null
    @Volatile private var submissionRepository: SubmissionRepository? = null
    @Volatile private var syncRepository: SyncRepository? = null
    @Volatile private var connectivityObserver: NetworkConnectivityObserver? = null

    fun sessionManager(context: Context): SessionManager =
        sessionManager ?: synchronized(this) {
            sessionManager ?: SessionManager(context.applicationContext).also { sessionManager = it }
        }

    fun apiService(context: Context): ApiService =
        apiService ?: synchronized(this) {
            apiService ?: NetworkModule.createApiService(sessionManager(context)).also { apiService = it }
        }

    fun database(context: Context): AppDatabase = AppDatabase.getInstance(context)

    fun authRepository(context: Context): AuthRepository =
        authRepository ?: synchronized(this) {
            authRepository ?: AuthRepository(apiService(context), sessionManager(context)).also { authRepository = it }
        }

    fun surveyRepository(context: Context): SurveyRepository =
        surveyRepository ?: synchronized(this) {
            surveyRepository ?: SurveyRepository(apiService(context), database(context).surveyDao()).also { surveyRepository = it }
        }

    fun submissionRepository(context: Context): SubmissionRepository =
        submissionRepository ?: synchronized(this) {
            submissionRepository ?: SubmissionRepository(database(context).submissionDao()).also { submissionRepository = it }
        }

    @Suppress("HardwareIds")
    fun syncRepository(context: Context): SyncRepository =
        syncRepository ?: synchronized(this) {
            val deviceId = Settings.Secure.getString(context.contentResolver, Settings.Secure.ANDROID_ID) ?: "unknown-device"
            syncRepository ?: SyncRepository(
                apiService(context),
                database(context).submissionDao(),
                submissionRepository(context),
                deviceId
            ).also { syncRepository = it }
        }

    fun connectivityObserver(context: Context): NetworkConnectivityObserver =
        connectivityObserver ?: synchronized(this) {
            connectivityObserver ?: NetworkConnectivityObserver(context.applicationContext).also { connectivityObserver = it }
        }
}
