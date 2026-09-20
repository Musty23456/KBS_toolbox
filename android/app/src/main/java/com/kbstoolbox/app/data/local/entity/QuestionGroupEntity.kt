package com.kbstoolbox.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "question_groups")
data class QuestionGroupEntity(
    @PrimaryKey val id: String,
    val surveyId: String,
    val surveyVersionId: String,
    val sectionId: String?,
    val title: String,
    val description: String?,
    val orderIndex: Int,
    val repeatable: Boolean,
    val minRepeats: Int,
    val maxRepeats: Int?
)
