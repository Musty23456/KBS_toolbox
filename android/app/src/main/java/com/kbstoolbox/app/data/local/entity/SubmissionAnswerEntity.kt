package com.kbstoolbox.app.data.local.entity

import androidx.room.Entity
import androidx.room.ForeignKey
import androidx.room.Index
import androidx.room.PrimaryKey

@Entity(
    tableName = "submission_answers",
    foreignKeys = [
        ForeignKey(
            entity = SubmissionEntity::class,
            parentColumns = ["clientSubmissionUuid"],
            childColumns = ["submissionUuid"],
            onDelete = ForeignKey.CASCADE
        )
    ],
    indices = [Index(value = ["submissionUuid"])]
)
data class SubmissionAnswerEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val submissionUuid: String,
    val questionId: String,
    val valueText: String?,
    /** Local file path (photo/audio/signature) or scanned code (barcode). */
    val mediaReference: String?,
    val groupInstanceIndex: Int? = null
)
