package com.kbstoolbox.app.data.remote.dto

data class ChoiceDto(
    val id: String,
    val value: String,
    val label: String,
    val order_index: Int,
    val cascade_parent_value: String?
)

data class QuestionGroupDto(
    val id: String,
    val title: String,
    val description: String?,
    val order_index: Int,
    val section_id: String?,
    val repeatable: Boolean,
    val min_repeats: Int,
    val max_repeats: Int?
)

data class QuestionDto(
    val id: String,
    val code: String,
    val label: String,
    val hint: String?,
    val type: String,
    val order_index: Int,
    val is_required: Boolean,
    val min_value: Double?,
    val max_value: Double?,
    val min_length: Int?,
    val max_length: Int?,
    val regex_pattern: String?,
    val relevance_expression: String?,
    val calculation_expression: String?,
    val default_value: String?,
    val cascade_parent_question_id: String?,
    val group_id: String?,
    val choices: List<ChoiceDto> = emptyList()
)

data class SurveyDetailDto(
    val id: String,
    val title: String,
    val description: String?,
    val status: String,
    val created_at: String,
    val current_version_number: Int?,
    val current_version_id: String?,
    val questions: List<QuestionDto> = emptyList(),
    val groups: List<QuestionGroupDto> = emptyList()
)
