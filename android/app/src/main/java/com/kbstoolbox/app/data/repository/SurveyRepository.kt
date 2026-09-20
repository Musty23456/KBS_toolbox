package com.kbstoolbox.app.data.repository

import com.kbstoolbox.app.data.local.dao.SurveyDao
import com.kbstoolbox.app.data.local.entity.ChoiceEntity
import com.kbstoolbox.app.data.local.entity.QuestionEntity
import com.kbstoolbox.app.data.local.entity.QuestionGroupEntity
import com.kbstoolbox.app.data.local.entity.SurveyEntity
import com.kbstoolbox.app.data.remote.ApiService
import com.kbstoolbox.app.data.remote.dto.SurveyDetailDto
import kotlinx.coroutines.flow.Flow

data class FormDefinition(
    val survey: SurveyEntity,
    val questions: List<QuestionEntity>,
    val choicesByQuestion: Map<String, List<ChoiceEntity>>,
    val groups: List<QuestionGroupEntity> = emptyList()
)

sealed class SyncDownloadResult {
    data class Success(val surveyCount: Int) : SyncDownloadResult()
    data class Error(val message: String) : SyncDownloadResult()
}

/**
 * Offline-first by design: every read comes from Room. `refreshFromServer`
 * is the only method that touches the network, and it is safe to call
 * whenever connectivity allows — it fully replaces each survey's cached
 * definition, so the device always renders the exact form the server most
 * recently published.
 */
class SurveyRepository(
    private val apiService: ApiService,
    private val surveyDao: SurveyDao
) {
    fun observeSurveys() = surveyDao.observeSurveys()

    fun observeQuestions(surveyId: String) = surveyDao.observeQuestions(surveyId)

    suspend fun getFormDefinition(surveyId: String): FormDefinition? {
        val survey = surveyDao.getSurvey(surveyId) ?: return null
        val questions = surveyDao.getQuestions(surveyId)
        val choices = surveyDao.getChoicesForQuestions(questions.map { it.id })
        val groups = surveyDao.getGroups(surveyId)
        return FormDefinition(survey, questions, choices.groupBy { it.questionId }, groups)
    }

    suspend fun refreshFromServer(): SyncDownloadResult {
        return try {
            val response = apiService.syncDownload()
            if (!response.isSuccessful || response.body() == null) {
                return SyncDownloadResult.Error("Server returned an error while downloading surveys.")
            }
            val surveys = response.body()!!.surveys
            val now = System.currentTimeMillis()

            for (dto in surveys) {
                cacheSurvey(dto, now)
            }
            surveyDao.pruneSurveysNotIn(surveys.map { it.id })

            SyncDownloadResult.Success(surveys.size)
        } catch (e: Exception) {
            SyncDownloadResult.Error("No connection to the server. Using the last downloaded surveys.")
        }
    }

    private suspend fun cacheSurvey(dto: SurveyDetailDto, cachedAt: Long) {
        val surveyEntity = SurveyEntity(
            id = dto.id,
            title = dto.title,
            description = dto.description,
            status = dto.status,
            currentVersionId = dto.current_version_id,
            currentVersionNumber = dto.current_version_number,
            createdAt = dto.created_at,
            cachedAt = cachedAt
        )
        val questionEntities = dto.questions.map { q ->
            QuestionEntity(
                id = q.id,
                surveyId = dto.id,
                surveyVersionId = dto.current_version_id ?: "",
                code = q.code,
                label = q.label,
                hint = q.hint,
                type = q.type,
                orderIndex = q.order_index,
                isRequired = q.is_required,
                minValue = q.min_value,
                maxValue = q.max_value,
                minLength = q.min_length,
                maxLength = q.max_length,
                regexPattern = q.regex_pattern,
                relevanceExpression = q.relevance_expression,
                calculationExpression = q.calculation_expression,
                defaultValue = q.default_value,
                cascadeParentQuestionId = q.cascade_parent_question_id,
                groupId = q.group_id
            )
        }
        val groupEntities = dto.groups.map { g -> QuestionGroupEntity(g.id, dto.id, dto.current_version_id ?: "", g.section_id, g.title, g.description, g.order_index, g.repeatable, g.min_repeats, g.max_repeats) }
        val choiceEntities = dto.questions.flatMap { q ->
            q.choices.map { c ->
                ChoiceEntity(
                    id = c.id,
                    questionId = q.id,
                    value = c.value,
                    label = c.label,
                    orderIndex = c.order_index,
                    cascadeParentValue = c.cascade_parent_value
                )
            }
        }
        surveyDao.replaceSurveyDefinition(surveyEntity, questionEntities, choiceEntities, groupEntities)
    }
}
