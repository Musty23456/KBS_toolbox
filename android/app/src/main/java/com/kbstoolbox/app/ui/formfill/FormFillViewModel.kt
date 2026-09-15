package com.kbstoolbox.app.ui.formfill

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.kbstoolbox.app.data.local.entity.ChoiceEntity
import com.kbstoolbox.app.data.local.entity.QuestionEntity
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

data class FormFillUiState(
    val isLoading: Boolean = true,
    val surveyTitle: String = "",
    val questions: List<QuestionEntity> = emptyList(),
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

    val visibleQuestions: List<QuestionEntity> get() = questions.filter { isVisible(it) }
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
            val textAnswers = existingAnswers.filter { it.valueText != null }.associate { it.questionId to it.valueText!! }
            val mediaAnswers = existingAnswers.filter { it.mediaReference != null }.associate { it.questionId to it.mediaReference!! }
            capturedGpsLat = submission.gpsLatitude
            capturedGpsLng = submission.gpsLongitude

            _uiState.value = FormFillUiState(
                isLoading = false,
                surveyTitle = definition.survey.title,
                questions = definition.questions,
                choicesByQuestion = definition.choicesByQuestion,
                textAnswers = textAnswers,
                mediaAnswers = mediaAnswers
            )
        }
    }

    fun submissionUuid(): String = if (::submission.isInitialized) submission.clientSubmissionUuid else ""

    fun updateTextAnswer(questionId: String, value: String) {
        val state = _uiState.value
        _uiState.value = state.copy(
            textAnswers = state.textAnswers + (questionId to value),
            validationErrors = state.validationErrors - questionId
        )
    }

    fun toggleMultipleChoice(questionId: String, choiceValue: String, checked: Boolean) {
        val state = _uiState.value
        val current = state.textAnswers[questionId]?.split("|")?.filter { it.isNotBlank() }?.toMutableSet() ?: mutableSetOf()
        if (checked) current.add(choiceValue) else current.remove(choiceValue)
        _uiState.value = state.copy(textAnswers = state.textAnswers + (questionId to current.joinToString("|")))
    }

    fun setMediaAnswer(questionId: String, reference: String) {
        val state = _uiState.value
        _uiState.value = state.copy(
            mediaAnswers = state.mediaAnswers + (questionId to reference),
            validationErrors = state.validationErrors - questionId
        )
    }

    fun onGpsCaptured(questionId: String, latitude: Double, longitude: Double) {
        capturedGpsLat = latitude
        capturedGpsLng = longitude
        updateTextAnswer(questionId, "$latitude,$longitude")
    }

    /** Choices for a cascading question are filtered by the parent question's current answer. */
    fun choicesFor(question: QuestionEntity): List<ChoiceEntity> {
        val all = _uiState.value.choicesByQuestion[question.id] ?: emptyList()
        val parentId = question.cascadeParentQuestionId ?: return all.sortedBy { it.orderIndex }
        val parentValue = _uiState.value.textAnswers[parentId] ?: return emptyList()
        return all.filter { it.cascadeParentValue == null || it.cascadeParentValue == parentValue }
            .sortedBy { it.orderIndex }
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
        val answerEntities = state.questions.mapNotNull { q ->
            val text = state.textAnswers[q.id]
            val media = state.mediaAnswers[q.id]
            if (text == null && media == null) null
            else SubmissionAnswerEntity(
                submissionUuid = submission.clientSubmissionUuid,
                questionId = q.id,
                valueText = text,
                mediaReference = media
            )
        }
        if (markComplete) {
            submissionRepository.completeSubmission(submission, answerEntities, capturedGpsLat, capturedGpsLng)
        } else {
            submissionRepository.saveDraftAnswers(submission, answerEntities, capturedGpsLat, capturedGpsLng)
        }
    }
}
