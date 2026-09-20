package com.kbstoolbox.app.ui.formfill

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.kbstoolbox.app.data.local.entity.ChoiceEntity
import com.kbstoolbox.app.data.local.entity.QuestionEntity
import com.kbstoolbox.app.data.local.entity.QuestionGroupEntity
import com.kbstoolbox.app.data.local.entity.SubmissionAnswerEntity
import com.kbstoolbox.app.data.local.entity.SubmissionEntity
import com.kbstoolbox.app.data.repository.SubmissionRepository
import com.kbstoolbox.app.data.repository.SurveyRepository
import com.kbstoolbox.app.expressions.AnswerValidator
import com.kbstoolbox.app.expressions.ExpressionEvaluator
import com.kbstoolbox.app.sync.SyncWorker
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

private fun answerKey(questionId: String, groupInstanceIndex: Int?): String =
    if (groupInstanceIndex == null) questionId else "$questionId#$groupInstanceIndex"

private fun splitAnswerKey(key: String): Pair<String, Int?> {
    val parts = key.split("#", limit = 2)
    return if (parts.size == 2) parts[0] to parts[1].toIntOrNull() else key to null
}

data class FormFillUiState(
    val isLoading: Boolean = true,
    val surveyTitle: String = "",
    val questions: List<QuestionEntity> = emptyList(),
    val groups: List<QuestionGroupEntity> = emptyList(),
    val groupInstances: Map<String, List<Int>> = emptyMap(),
    val choicesByQuestion: Map<String, List<ChoiceEntity>> = emptyMap(),
    val textAnswers: Map<String, String> = emptyMap(),
    val mediaAnswers: Map<String, String> = emptyMap(),
    val validationErrors: Map<String, String> = emptyMap(),
    val isSaving: Boolean = false,
    val isSubmitted: Boolean = false,
    val errorMessage: String? = null
) {
    /** Answers keyed by question CODE (not id), for relevance/calculation expressions. */
    fun answersByCode(): Map<String, Any?> {
        val codeById = questions.associate { it.id to it.code }
        val result = mutableMapOf<String, Any?>()
        textAnswers.forEach { (qid, value) ->
            codeById[qid]?.let { code -> result[code] = value.toDoubleOrNull() ?: value }
        }
        return result
    }

    fun isVisible(question: QuestionEntity): Boolean =
        ExpressionEvaluator.isRelevant(question.relevanceExpression, answersByCode())

    fun isVisible(question: QuestionEntity, groupInstanceIndex: Int): Boolean {
        if (question.groupId == null) return isVisible(question)
        val codeById = questions.filter { it.groupId == question.groupId }.associate { it.id to it.code }
        val values = mutableMapOf<String, Any?>()
        textAnswers.forEach { (key, value) ->
            val (qid, instance) = splitAnswerKey(key)
            if (instance == groupInstanceIndex) codeById[qid]?.let { code -> values[code] = value.toDoubleOrNull() ?: value }
        }
        return ExpressionEvaluator.isRelevant(question.relevanceExpression, values)
    }

    val visibleQuestions: List<QuestionEntity> get() = questions.filter { it.groupId == null && isVisible(it) }
}

class FormFillViewModel(
    private val surveyRepository: SurveyRepository,
    private val submissionRepository: SubmissionRepository,
    private val appContext: Context
) : ViewModel() {

    private val _uiState = MutableStateFlow(FormFillUiState())
    val uiState: StateFlow<FormFillUiState> = _uiState.asStateFlow()

    private lateinit var submission: SubmissionEntity
    private var capturedGpsLat: Double? = null
    private var capturedGpsLng: Double? = null

    fun load(surveyId: String, existingSubmissionUuid: String?) {
        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isLoading = true)
            val definition = surveyRepository.getFormDefinition(surveyId)
            if (definition == null) {
                _uiState.value = _uiState.value.copy(isLoading = false, errorMessage = "This survey is no longer available offline.")
                return@launch
            }

            submission = submissionRepository.getOrCreateDraft(
                surveyId = surveyId,
                surveyVersionId = definition.survey.currentVersionId ?: "",
                surveyTitle = definition.survey.title,
                existingUuid = existingSubmissionUuid
            )
            val existingAnswers = submissionRepository.getAnswers(submission.clientSubmissionUuid)
            val groups = definition.groups.sortedBy { it.orderIndex }
            val instances = groups.associate { group ->
                val indexes = existingAnswers.filter { answer ->
                    answer.groupInstanceIndex != null && definition.questions.any { it.id == answer.questionId && it.groupId == group.id }
                }.mapNotNull { it.groupInstanceIndex }.distinct().sorted()
                group.id to if (group.repeatable) {
                    if (indexes.isEmpty()) listOf(0) else indexes
                } else listOf(0)
            }
            val textAnswers = existingAnswers.filter { it.valueText != null }.associate { answer -> answerKey(answer.questionId, answer.groupInstanceIndex) to answer.valueText!! }
            val mediaAnswers = existingAnswers.filter { it.mediaReference != null }.associate { answer -> answerKey(answer.questionId, answer.groupInstanceIndex) to answer.mediaReference!! }
            capturedGpsLat = submission.gpsLatitude
            capturedGpsLng = submission.gpsLongitude

            _uiState.value = FormFillUiState(
                isLoading = false,
                surveyTitle = definition.survey.title,
                questions = definition.questions,
                groups = groups,
                groupInstances = instances,
                choicesByQuestion = definition.choicesByQuestion,
                textAnswers = textAnswers,
                mediaAnswers = mediaAnswers
            )
        }
    }

    fun submissionUuid(): String = if (::submission.isInitialized) submission.clientSubmissionUuid else ""

    fun updateTextAnswer(questionId: String, value: String, groupInstanceIndex: Int? = null) {
        val state = _uiState.value
        _uiState.value = state.copy(
            textAnswers = state.textAnswers + (answerKey(questionId, groupInstanceIndex) to value),
            validationErrors = state.validationErrors - answerKey(questionId, groupInstanceIndex)
        )
    }

    fun toggleMultipleChoice(questionId: String, choiceValue: String, checked: Boolean, groupInstanceIndex: Int? = null) {
        val state = _uiState.value
        val key = answerKey(questionId, groupInstanceIndex)
        val current = state.textAnswers[key]?.split("|")?.filter { it.isNotBlank() }?.toMutableSet() ?: mutableSetOf()
        if (checked) current.add(choiceValue) else current.remove(choiceValue)
        _uiState.value = state.copy(textAnswers = state.textAnswers + (key to current.joinToString("|")))
    }

    fun setMediaAnswer(questionId: String, reference: String, groupInstanceIndex: Int? = null) {
        val state = _uiState.value
        _uiState.value = state.copy(
            mediaAnswers = state.mediaAnswers + (answerKey(questionId, groupInstanceIndex) to reference),
            validationErrors = state.validationErrors - answerKey(questionId, groupInstanceIndex)
        )
    }

    fun onGpsCaptured(questionId: String, latitude: Double, longitude: Double, groupInstanceIndex: Int? = null) {
        capturedGpsLat = latitude
        capturedGpsLng = longitude
        updateTextAnswer(questionId, "$latitude,$longitude", groupInstanceIndex)
    }

    /** Choices for a cascading question are filtered by the parent question's current answer. */
    fun choicesFor(question: QuestionEntity): List<ChoiceEntity> {
        val all = _uiState.value.choicesByQuestion[question.id] ?: emptyList()
        val parentId = question.cascadeParentQuestionId ?: return all.sortedBy { it.orderIndex }
        val parentValue = _uiState.value.textAnswers[parentId] ?: return emptyList()
        return all.filter { it.cascadeParentValue == null || it.cascadeParentValue == parentValue }
            .sortedBy { it.orderIndex }
    }

    fun addGroupInstance(groupId: String) {
        val state = _uiState.value
        val group = state.groups.firstOrNull { it.id == groupId } ?: return
        if (!group.repeatable) return
        val current = state.groupInstances[groupId] ?: listOf(0)
        if (group.maxRepeats != null && current.size >= group.maxRepeats) return
        val next = (current.maxOrNull() ?: -1) + 1
        _uiState.value = state.copy(groupInstances = state.groupInstances + (groupId to (current + next)))
    }

    fun removeGroupInstance(groupId: String, instanceIndex: Int) {
        val state = _uiState.value
        val group = state.groups.firstOrNull { it.id == groupId } ?: return
        if (!group.repeatable || instanceIndex == 0) return
        val current = state.groupInstances[groupId] ?: return
        if (current.size <= group.minRepeats) return
        val newInstances = current.filterNot { it == instanceIndex }
        val prefix = state.groups.filter { it.id == groupId }.flatMap { g -> state.questions.filter { it.groupId == g.id } }
        val text = state.textAnswers.toMutableMap()
        val media = state.mediaAnswers.toMutableMap()
        prefix.forEach { q ->
            text.remove(answerKey(q.id, instanceIndex))
            media.remove(answerKey(q.id, instanceIndex))
        }
        _uiState.value = state.copy(groupInstances = state.groupInstances + (groupId to newInstances), textAnswers = text, mediaAnswers = media)
    }

    fun saveDraft(onSaved: () -> Unit) {
        viewModelScope.launch {
            persistCurrentAnswers(markComplete = false)
            onSaved()
        }
    }

    fun submit() {
        val state = _uiState.value
        val issues = AnswerValidator.validate(state.questions.filter { state.isVisible(it) }, allAnswersAsText())
        if (issues.isNotEmpty()) {
            val errorsByQuestionId = state.questions.associateBy { it.code }
            val errorMap = issues.mapNotNull { issue ->
                errorsByQuestionId[issue.questionCode]?.let { it.id to issue.message }
            }.toMap()
            _uiState.value = state.copy(validationErrors = errorMap, errorMessage = "Please fix the highlighted fields.")
            return
        }

        viewModelScope.launch {
            _uiState.value = _uiState.value.copy(isSaving = true)
            persistCurrentAnswers(markComplete = true)
            SyncWorker.triggerImmediateSync(appContext)
            _uiState.value = _uiState.value.copy(isSaving = false, isSubmitted = true)
        }
    }

    private fun allAnswersAsText(): Map<String, String?> {
        val state = _uiState.value
        val combined = mutableMapOf<String, String?>()
        state.questions.forEach { q ->
            combined[q.id] = state.textAnswers[q.id] ?: state.mediaAnswers[q.id]
        }
        return combined
    }

    private suspend fun persistCurrentAnswers(markComplete: Boolean) {
        val state = _uiState.value
        val answerEntities = (state.textAnswers.keys + state.mediaAnswers.keys).distinct().mapNotNull { key ->
            val (questionId, instanceIndex) = splitAnswerKey(key)
            val text = state.textAnswers[key]
            val media = state.mediaAnswers[key]
            if (text == null && media == null) null
            else SubmissionAnswerEntity(
                submissionUuid = submission.clientSubmissionUuid,
                questionId = questionId,
                valueText = text,
                mediaReference = media,
                groupInstanceIndex = instanceIndex
            )
        }
        if (markComplete) {
            submissionRepository.completeSubmission(submission, answerEntities, capturedGpsLat, capturedGpsLng)
        } else {
            submissionRepository.saveDraftAnswers(submission, answerEntities, capturedGpsLat, capturedGpsLng)
        }
    }
}
