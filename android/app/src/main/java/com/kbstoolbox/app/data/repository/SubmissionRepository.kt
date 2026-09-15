package com.kbstoolbox.app.data.repository

import com.kbstoolbox.app.data.local.dao.SubmissionDao
import com.kbstoolbox.app.data.local.entity.LocalSyncStatus
import com.kbstoolbox.app.data.local.entity.SubmissionAnswerEntity
import com.kbstoolbox.app.data.local.entity.SubmissionEntity
import java.util.UUID

class SubmissionRepository(private val submissionDao: SubmissionDao) {

    fun observeAll() = submissionDao.observeAll()

    fun observePendingCount() = submissionDao.countByStatus(LocalSyncStatus.PENDING_SYNC)
    fun observeSyncedCount() = submissionDao.countByStatus(LocalSyncStatus.SYNCED)
    fun observeDraftCount() = submissionDao.countByStatus(LocalSyncStatus.DRAFT)
    fun observeFailedCount() = submissionDao.countByStatus(LocalSyncStatus.FAILED)

    suspend fun getAnswers(uuid: String) = submissionDao.getAnswers(uuid)

    suspend fun getOrCreateDraft(surveyId: String, surveyVersionId: String, surveyTitle: String, existingUuid: String?): SubmissionEntity {
        existingUuid?.let { uuid ->
            submissionDao.getByUuid(uuid)?.let { return it }
        }
        val now = System.currentTimeMillis()
        val draft = SubmissionEntity(
            clientSubmissionUuid = UUID.randomUUID().toString(),
            surveyId = surveyId,
            surveyVersionId = surveyVersionId,
            surveyTitle = surveyTitle,
            status = LocalSyncStatus.DRAFT,
            gpsLatitude = null,
            gpsLongitude = null,
            collectedAt = null,
            createdAt = now,
            updatedAt = now
        )
        submissionDao.insertSubmission(draft)
        return draft
    }

    /**
     * Persists the current answers for a draft-in-progress without marking
     * it complete, so an enumerator can back out of a partially-filled form
     * and resume later — including after the app is killed or the device
     * loses power, since this writes to Room immediately, not just memory.
     */
    suspend fun saveDraftAnswers(
        submission: SubmissionEntity,
        answers: List<SubmissionAnswerEntity>,
        gpsLatitude: Double?,
        gpsLongitude: Double?
    ) {
        val updated = submission.copy(
            gpsLatitude = gpsLatitude ?: submission.gpsLatitude,
            gpsLongitude = gpsLongitude ?: submission.gpsLongitude,
            updatedAt = System.currentTimeMillis()
        )
        submissionDao.saveSubmissionWithAnswers(updated, answers)
    }

    /**
     * Marks a submission complete and ready to sync. This never touches the
     * network directly — it only flips local state to PENDING_SYNC; the
     * WorkManager-scheduled SyncWorker (or a manual "sync now" trigger)
     * picks it up whenever connectivity allows.
     */
    suspend fun completeSubmission(
        submission: SubmissionEntity,
        answers: List<SubmissionAnswerEntity>,
        gpsLatitude: Double?,
        gpsLongitude: Double?
    ) {
        val nowIso = currentIsoTimestamp()
        val completed = submission.copy(
            status = LocalSyncStatus.PENDING_SYNC,
            gpsLatitude = gpsLatitude ?: submission.gpsLatitude,
            gpsLongitude = gpsLongitude ?: submission.gpsLongitude,
            collectedAt = submission.collectedAt ?: nowIso,
            updatedAt = System.currentTimeMillis()
        )
        submissionDao.saveSubmissionWithAnswers(completed, answers)
    }

    private fun currentIsoTimestamp(): String {
        // Manual ISO-8601 UTC formatting rather than java.time.Instant, which
        // requires API 26+ (or core library desugaring) — this keeps minSdk 24
        // support with no extra Gradle configuration.
        val format = java.text.SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", java.util.Locale.US)
        format.timeZone = java.util.TimeZone.getTimeZone("UTC")
        return format.format(java.util.Date())
    }

    suspend fun getPendingForSync(): List<SubmissionEntity> = submissionDao.getByStatus(LocalSyncStatus.PENDING_SYNC) +
        submissionDao.getByStatus(LocalSyncStatus.FAILED)
}
