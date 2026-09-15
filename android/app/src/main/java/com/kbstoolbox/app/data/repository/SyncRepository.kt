package com.kbstoolbox.app.data.repository

import com.kbstoolbox.app.data.local.dao.SubmissionDao
import com.kbstoolbox.app.data.local.entity.LocalSyncStatus
import com.kbstoolbox.app.data.remote.ApiService
import com.kbstoolbox.app.data.remote.dto.AnswerDto
import com.kbstoolbox.app.data.remote.dto.SubmissionCreateDto
import com.kbstoolbox.app.data.remote.dto.SyncUploadRequestDto

sealed class SyncUploadOutcome {
    data class Completed(val uploaded: Int, val failed: Int) : SyncUploadOutcome()
    data class NetworkUnavailable(val message: String) : SyncUploadOutcome()
}

class SyncRepository(
    private val apiService: ApiService,
    private val submissionDao: SubmissionDao,
    private val submissionRepository: SubmissionRepository,
    private val deviceId: String
) {
    suspend fun uploadPendingSubmissions(): SyncUploadOutcome {
        val pending = submissionRepository.getPendingForSync()
        if (pending.isEmpty()) return SyncUploadOutcome.Completed(0, 0)

        val now = System.currentTimeMillis()
        pending.forEach { submissionDao.updateStatus(it.clientSubmissionUuid, LocalSyncStatus.SYNCING, now) }

        val payloadItems = pending.map { submission ->
            val answers = submissionDao.getAnswers(submission.clientSubmissionUuid).map {
                AnswerDto(question_id = it.questionId, value_text = it.valueText, media_reference = it.mediaReference)
            }
            SubmissionCreateDto(
                client_submission_uuid = submission.clientSubmissionUuid,
                survey_id = submission.surveyId,
                survey_version_id = submission.surveyVersionId,
                collected_at = submission.collectedAt,
                gps_latitude = submission.gpsLatitude,
                gps_longitude = submission.gpsLongitude,
                answers = answers
            )
        }

        return try {
            val response = apiService.syncUpload(SyncUploadRequestDto(device_id = deviceId, submissions = payloadItems))
            if (!response.isSuccessful || response.body() == null) {
                markAllFailed(pending.map { it.clientSubmissionUuid }, "Server rejected the sync batch (${response.code()}).")
                return SyncUploadOutcome.Completed(0, pending.size)
            }

            var uploaded = 0
            var failed = 0
            val resultsByUuid = response.body()!!.results.associateBy { it.client_submission_uuid }
            val finishTime = System.currentTimeMillis()

            for (submission in pending) {
                val result = resultsByUuid[submission.clientSubmissionUuid]
                if (result != null && result.accepted) {
                    submissionDao.updateSyncResult(
                        submission.clientSubmissionUuid, LocalSyncStatus.SYNCED, result.server_submission_id, null, finishTime
                    )
                    uploaded++
                } else {
                    submissionDao.updateSyncResult(
                        submission.clientSubmissionUuid, LocalSyncStatus.FAILED, null,
                        result?.error ?: "No response for this submission.", finishTime
                    )
                    failed++
                }
            }
            SyncUploadOutcome.Completed(uploaded, failed)
        } catch (e: Exception) {
            markAllFailed(pending.map { it.clientSubmissionUuid }, "Could not reach the server.")
            SyncUploadOutcome.NetworkUnavailable("Could not reach the server. Will retry automatically.")
        }
    }

    private suspend fun markAllFailed(uuids: List<String>, error: String) {
        val now = System.currentTimeMillis()
        uuids.forEach { submissionDao.updateSyncResult(it, LocalSyncStatus.FAILED, null, error, now) }
    }
}
