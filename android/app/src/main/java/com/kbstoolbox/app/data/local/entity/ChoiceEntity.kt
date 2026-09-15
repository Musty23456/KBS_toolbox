package com.kbstoolbox.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "choices")
data class ChoiceEntity(
    @PrimaryKey val id: String,
    val questionId: String,
    val value: String,
    val label: String,
    val orderIndex: Int,
    val cascadeParentValue: String?
)
