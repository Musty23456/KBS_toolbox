package com.kbstoolbox.app.sync

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import androidx.work.Constraints
import com.kbstoolbox.app.di.ServiceLocator
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.util.concurrent.TimeUnit

/**
 * Uploads any offline-queued submissions and refreshes cached survey
 * definitions whenever the device has connectivity. Safe to run repeatedly:
 * uploads are idempotent server-side (client_submission_uuid), and survey
 * refresh fully replaces each definition rather than merging.
 */
class SyncWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result = withContext(Dispatchers.IO) {
        val appContext = applicationContext
        val connectivity = ServiceLocator.connectivityObserver(appContext)
        if (!connectivity.isCurrentlyOnline()) {
            return@withContext Result.retry()
        }

        return@withContext try {
            val syncRepository = ServiceLocator.syncRepository(appContext)
            val surveyRepository = ServiceLocator.surveyRepository(appContext)

            syncRepository.uploadPendingSubmissions()
            surveyRepository.refreshFromServer()

            Result.success()
        } catch (e: Exception) {
            Result.retry()
        }
    }

    companion object {
        private const val PERIODIC_WORK_NAME = "kbs_toolbox_periodic_sync"
        private const val ONE_TIME_WORK_NAME = "kbs_toolbox_manual_sync"

        /** Schedules a background sync roughly every 15 minutes while connected — the WorkManager minimum interval. */
        fun schedulePeriodic(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val request = PeriodicWorkRequestBuilder<SyncWorker>(15, TimeUnit.MINUTES)
                .setConstraints(constraints)
                .build()

            WorkManager.getInstance(context).enqueueUniquePeriodicWork(
                PERIODIC_WORK_NAME,
                ExistingPeriodicWorkPolicy.KEEP,
                request
            )
        }

        /** Triggers an immediate sync attempt, e.g. right after a submission is completed or the user taps "Sync now". */
        fun triggerImmediateSync(context: Context) {
            val constraints = Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()

            val request = OneTimeWorkRequestBuilder<SyncWorker>()
                .setConstraints(constraints)
                .build()

            WorkManager.getInstance(context).enqueueUniqueWork(
                ONE_TIME_WORK_NAME,
                ExistingWorkPolicy.REPLACE,
                request
            )
        }
    }
}
