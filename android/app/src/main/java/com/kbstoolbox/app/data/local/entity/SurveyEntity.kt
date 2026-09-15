package com.kbstoolbox.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "surveys")
data class SurveyEntity(
    @PrimaryKey val id: String,
    val title: String,
    val description: String?,
    val status: String,
    val currentVersionId: String?,
    val currentVersionNumber: Int?,
    val createdAt: String,
    /** When this survey definition was last refreshed from the server. */
    val cachedAt: Long
)
