package com.kbstoolbox.app.data.repository

import com.kbstoolbox.app.data.local.dao.SubmissionDao
import com.kbstoolbox.app.data.local.entity.LocalSyncStatus
import com.kbstoolbox.app.data.remote.ApiService
import com.kbstoolbox.app.data.remote.dto.AnswerDto
import com.kbstoolbox.app.data.remote.dto.DeviceHeartbeatDto
import com.kbstoolbox.app.BuildConfig
import com.kbstoolbox.app.data.remote.dto.SubmissionCreateDto
import com.kbstoolbox.app.data.remote.dto.SyncUploadRequestDto
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File

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
        if (pending.isEmpty()) {
            try { apiService.deviceHeartbeat(DeviceHeartbeatDto(deviceId, BuildConfig.VERSION_NAME)) } catch (_: Exception) {}
            return SyncUploadOutcome.Completed(0, 0)
        }

        val now = System.currentTimeMillis()
        pending.forEach { submissionDao.updateStatus(it.clientSubmissionUuid, LocalSyncStatus.SYNCING, now) }

        val payloadItems = pending.map { submission ->
            val answers = submissionDao.getAnswers(submission.clientSubmissionUuid).map {
                AnswerDto(question_id = it.questionId, value_text = it.valueText, media_reference = it.mediaReference, group_instance_index = it.groupInstanceIndex)
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
                    val mediaUploadFailed = result.server_submission_id?.let {
                        uploadLocalMedia(submission.clientSubmissionUuid, it)
                    } ?: 0
                    submissionDao.updateSyncResult(
                        submission.clientSubmissionUuid,
                        if (mediaUploadFailed == 0) LocalSyncStatus.SYNCED else LocalSyncStatus.FAILED,
                        result.server_submission_id,
                        if (mediaUploadFailed == 0) null else "$mediaUploadFailed media file(s) failed to upload.",
                        finishTime
                    )
                    if (mediaUploadFailed == 0) uploaded++ else failed++
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


    private suspend fun uploadLocalMedia(localUuid: String, serverSubmissionId: String): Int {
        var failed = 0
        val answers = submissionDao.getAnswers(localUuid)
        for (answer in answers) {
            val path = answer.mediaReference ?: continue
            if (path.startsWith("http://") || path.startsWith("https://") || path.startsWith("/api/media/")) continue
            val file = File(path)
            if (!file.isFile) { failed++; continue }
            val kind = when (file.extension.lowercase()) {
                "m4a", "mp3", "aac", "wav", "ogg" -> "AUDIO"
                "png" -> "SIGNATURE"
                "jpg", "jpeg", "webp" -> "PHOTO"
                else -> continue
            }
            try {
                val mime = when (kind) {
                    "AUDIO" -> "audio/mp4"
                    "SIGNATURE" -> "image/png"
                    else -> "image/jpeg"
                }
                val requestFile = file.asRequestBody(mime.toMediaTypeOrNull())
                val body = MultipartBody.Part.createFormData("file", file.name, requestFile)
                val response = apiService.uploadMedia(
                    serverSubmissionId.toRequestBody("text/plain".toMediaTypeOrNull()),
                    answer.questionId.toRequestBody("text/plain".toMediaTypeOrNull()),
                    kind.toRequestBody("text/plain".toMediaTypeOrNull()),
                    answer.groupInstanceIndex?.toString()?.toRequestBody("text/plain".toMediaTypeOrNull()),
                    body
                )
                if (response.isSuccessful && response.body() != null) {
                    submissionDao.updateMediaReference(answer.id, response.body()!!.url)
                } else {
                    failed++
                }
            } catch (_: Exception) {
                failed++
            }
        }
        return failed
    }

    private suspend fun markAllFailed(uuids: List<String>, error: String) {
        val now = System.currentTimeMillis()
        uuids.forEach { submissionDao.updateSyncResult(it, LocalSyncStatus.FAILED, null, error, now) }
    }
}
