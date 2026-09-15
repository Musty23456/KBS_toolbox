package com.kbstoolbox.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * Local sync lifecycle for one submission. Mirrors the states called out in
 * the product spec: a form is DRAFT while being filled, becomes PENDING_SYNC
 * once the enumerator finishes it, SYNCING while an upload attempt is in
 * flight, and ends at SYNCED or FAILED (with FAILED retried automatically by
 * the next WorkManager run while connectivity is available).
 */
enum class LocalSyncStatus {
    DRAFT,
    PENDING_SYNC,
    SYNCING,
    SYNCED,
    FAILED
}

@Entity(tableName = "submissions")
data class SubmissionEntity(
    /** Client-generated at creation time; doubles as the server idempotency key. */
    @PrimaryKey val clientSubmissionUuid: String,
    val surveyId: String,
    val surveyVersionId: String,
    val surveyTitle: String,
    val status: LocalSyncStatus,
    val gpsLatitude: Double?,
    val gpsLongitude: Double?,
    val collectedAt: String?,
    val createdAt: Long,
    val updatedAt: Long,
    val serverSubmissionId: String? = null,
    val syncErrorMessage: String? = null,
    val syncAttemptCount: Int = 0
)
