package com.kbstoolbox.app.data.remote.dto

data class AnswerDto(
    val question_id: String,
    val value_text: String?,
    val media_reference: String?,
    val group_instance_index: Int? = null
)

data class SubmissionCreateDto(
    val client_submission_uuid: String,
    val survey_id: String,
    val survey_version_id: String,
    val collected_at: String?,
    val gps_latitude: Double?,
    val gps_longitude: Double?,
    val answers: List<AnswerDto>
)

data class SubmissionResponseDto(
    val id: String,
    val survey_id: String,
    val survey_version_id: String,
    val submitted_by_id: String,
    val client_submission_uuid: String,
    val status: String,
    val gps_latitude: Double?,
    val gps_longitude: Double?,
    val collected_at: String?,
    val synced_at: String?,
    val created_at: String,
    val answers: List<AnswerDto> = emptyList()
)

data class SyncUploadRequestDto(
    val device_id: String,
    val submissions: List<SubmissionCreateDto>
)

data class SyncUploadResultItemDto(
    val client_submission_uuid: String,
    val accepted: Boolean,
    val server_submission_id: String?,
    val error: String?
)

data class SyncUploadResponseDto(
    val results: List<SyncUploadResultItemDto>
)

data class SyncDownloadResponseDto(
    val surveys: List<SurveyDetailDto>,
    val server_time: String
)


data class MediaUploadResponseDto(
    val id: String,
    val url: String,
    val kind: String,
    val size_bytes: Long
)


data class DeviceHeartbeatDto(
    val device_id: String,
    val app_version: String?,
    val platform: String = "ANDROID"
)
