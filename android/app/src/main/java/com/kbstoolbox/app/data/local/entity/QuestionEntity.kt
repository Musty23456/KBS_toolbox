package com.kbstoolbox.app.data.local.entity

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "questions")
data class QuestionEntity(
    @PrimaryKey val id: String,
    val surveyId: String,
    val surveyVersionId: String,
    val code: String,
    val label: String,
    val hint: String?,
    val type: String,
    val orderIndex: Int,
    val isRequired: Boolean,
    val minValue: Double?,
    val maxValue: Double?,
    val minLength: Int?,
    val maxLength: Int?,
    val regexPattern: String?,
    val relevanceExpression: String?,
    val calculationExpression: String?,
    val defaultValue: String?,
    val cascadeParentQuestionId: String?
)
