package com.kbstoolbox.app.data.local.dao

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query
import androidx.room.Transaction
import com.kbstoolbox.app.data.local.entity.ChoiceEntity
import com.kbstoolbox.app.data.local.entity.QuestionEntity
import com.kbstoolbox.app.data.local.entity.SurveyEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface SurveyDao {

    @Query("SELECT * FROM surveys ORDER BY title ASC")
    fun observeSurveys(): Flow<List<SurveyEntity>>

    @Query("SELECT * FROM surveys WHERE id = :surveyId")
    suspend fun getSurvey(surveyId: String): SurveyEntity?

    @Query("SELECT * FROM questions WHERE surveyId = :surveyId ORDER BY orderIndex ASC")
    fun observeQuestions(surveyId: String): Flow<List<QuestionEntity>>

    @Query("SELECT * FROM questions WHERE surveyId = :surveyId ORDER BY orderIndex ASC")
    suspend fun getQuestions(surveyId: String): List<QuestionEntity>

    @Query("SELECT * FROM choices WHERE questionId IN (:questionIds)")
    suspend fun getChoicesForQuestions(questionIds: List<String>): List<ChoiceEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertSurveys(surveys: List<SurveyEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertQuestions(questions: List<QuestionEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertChoices(choices: List<ChoiceEntity>)

    @Query("DELETE FROM questions WHERE surveyId = :surveyId")
    suspend fun deleteQuestionsForSurvey(surveyId: String)

    @Query("DELETE FROM choices WHERE questionId IN (SELECT id FROM questions WHERE surveyId = :surveyId)")
    suspend fun deleteChoicesForSurvey(surveyId: String)

    /**
     * Replaces the entire cached definition of one survey (survey row +
     * questions + choices) atomically, so a device is never left with a
     * question set from one version mixed with choices from another.
     */
    @Transaction
    suspend fun replaceSurveyDefinition(
        survey: SurveyEntity,
        questions: List<QuestionEntity>,
        choices: List<ChoiceEntity>
    ) {
        deleteChoicesForSurvey(survey.id)
        deleteQuestionsForSurvey(survey.id)
        insertSurveys(listOf(survey))
        insertQuestions(questions)
        insertChoices(choices)
    }

    @Query("DELETE FROM surveys WHERE id NOT IN (:keepIds)")
    suspend fun pruneSurveysNotIn(keepIds: List<String>)
}
