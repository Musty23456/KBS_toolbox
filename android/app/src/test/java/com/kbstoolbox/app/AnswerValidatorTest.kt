package com.kbstoolbox.app

import com.google.common.truth.Truth.assertThat
import com.kbstoolbox.app.data.local.entity.QuestionEntity
import com.kbstoolbox.app.expressions.AnswerValidator
import org.junit.Test

class AnswerValidatorTest {

    private fun question(
        id: String,
        code: String,
        type: String,
        required: Boolean = false,
        minValue: Double? = null,
        maxValue: Double? = null,
        minLength: Int? = null,
        maxLength: Int? = null,
        regex: String? = null,
        relevance: String? = null
    ) = QuestionEntity(
        id = id,
        surveyId = "survey-1",
        surveyVersionId = "version-1",
        code = code,
        label = code,
        hint = null,
        type = type,
        orderIndex = 0,
        isRequired = required,
        minValue = minValue,
        maxValue = maxValue,
        minLength = minLength,
        maxLength = maxLength,
        regexPattern = regex,
        relevanceExpression = relevance,
        calculationExpression = null,
        defaultValue = null,
        cascadeParentQuestionId = null
    )

    @Test
    fun `required field missing produces an issue`() {
        val q = question("q1", "full_name", "SHORT_TEXT", required = true)
        val issues = AnswerValidator.validate(listOf(q), mapOf("q1" to null))
        assertThat(issues).hasSize(1)
        assertThat(issues[0].questionCode).isEqualTo("full_name")
    }

    @Test
    fun `numeric range enforced`() {
        val q = question("q1", "age_years", "INTEGER", minValue = 0.0, maxValue = 120.0)
        assertThat(AnswerValidator.validate(listOf(q), mapOf("q1" to "150"))).isNotEmpty()
        assertThat(AnswerValidator.validate(listOf(q), mapOf("q1" to "40"))).isEmpty()
    }

    @Test
    fun `hidden question via relevance is not validated`() {
        val gender = question("q1", "gender", "SHORT_TEXT")
        val pregnancy = question(
            "q2", "is_pregnant", "SHORT_TEXT", required = true,
            relevance = "gender == 'FEMALE'"
        )
        val issues = AnswerValidator.validate(
            listOf(gender, pregnancy),
            mapOf("q1" to "MALE", "q2" to null)
        )
        assertThat(issues).isEmpty()
    }

    @Test
    fun `visible required question via relevance is validated`() {
        val gender = question("q1", "gender", "SHORT_TEXT")
        val pregnancy = question(
            "q2", "is_pregnant", "SHORT_TEXT", required = true,
            relevance = "gender == 'FEMALE'"
        )
        val issues = AnswerValidator.validate(
            listOf(gender, pregnancy),
            mapOf("q1" to "FEMALE", "q2" to null)
        )
        assertThat(issues).hasSize(1)
    }

    @Test
    fun `regex pattern enforced on text`() {
        val q = question("q1", "reg_number", "SHORT_TEXT", regex = "^[A-Z0-9-]+$")
        assertThat(AnswerValidator.validate(listOf(q), mapOf("q1" to "not valid!!"))).isNotEmpty()
        assertThat(AnswerValidator.validate(listOf(q), mapOf("q1" to "ABC-123"))).isEmpty()
    }
}
