package com.kbstoolbox.app

import com.google.common.truth.Truth.assertThat
import com.kbstoolbox.app.expressions.ExpressionEvaluator
import org.junit.Test

class ExpressionEvaluatorTest {

    @Test
    fun `simple equality`() {
        assertThat(ExpressionEvaluator.evaluate("gender == 'FEMALE'", mapOf("gender" to "FEMALE"))).isEqualTo(true)
        assertThat(ExpressionEvaluator.evaluate("gender == 'FEMALE'", mapOf("gender" to "MALE"))).isEqualTo(false)
    }

    @Test
    fun `boolean and with range`() {
        assertThat(
            ExpressionEvaluator.evaluate("age_years >= 18 and age_years < 65", mapOf("age_years" to 25.0))
        ).isEqualTo(true)
        assertThat(
            ExpressionEvaluator.evaluate("age_years >= 18 and age_years < 65", mapOf("age_years" to 70.0))
        ).isEqualTo(false)
    }

    @Test
    fun `arithmetic calculation`() {
        assertThat(ExpressionEvaluator.evaluate("household_size * 12", mapOf("household_size" to 4.0))).isEqualTo(48.0)
    }

    @Test
    fun `missing variable treated as null, comparisons are false`() {
        assertThat(ExpressionEvaluator.evaluate("gender == 'FEMALE'", emptyMap())).isEqualTo(false)
    }

    @Test
    fun `is relevant defaults true when blank`() {
        assertThat(ExpressionEvaluator.isRelevant(null, emptyMap())).isTrue()
        assertThat(ExpressionEvaluator.isRelevant("", emptyMap())).isTrue()
    }

    @Test
    fun `is relevant fails open on broken expression`() {
        assertThat(ExpressionEvaluator.isRelevant("this is not valid ((( at all", emptyMap())).isTrue()
    }

    @Test
    fun `or and not operators`() {
        assertThat(ExpressionEvaluator.evaluate("not (a == 'X')", mapOf("a" to "Y"))).isEqualTo(true)
        assertThat(ExpressionEvaluator.evaluate("a == 'X' or b == 'Y'", mapOf("a" to "Z", "b" to "Y"))).isEqualTo(true)
    }
}
