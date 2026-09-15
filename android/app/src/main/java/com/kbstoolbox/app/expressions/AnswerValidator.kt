package com.kbstoolbox.app.expressions

import com.kbstoolbox.app.data.local.entity.QuestionEntity

/**
 * Mirrors app/services/validation.py on the backend so an enumerator sees a
 * validation error immediately, offline, rather than only discovering it
 * once the submission is finally synced and rejected. This is a convenience
 * for the field, not a security boundary — the server always re-validates
 * independently before accepting a submission.
 */
object AnswerValidator {

    data class ValidationIssue(val questionCode: String, val message: String)

    fun validate(
        questions: List<QuestionEntity>,
        answersByQuestionId: Map<String, String?>
    ): List<ValidationIssue> {
        val issues = mutableListOf<ValidationIssue>()

        val answersByCode = mutableMapOf<String, Any?>()
        val codeById = questions.associate { it.id to it.code }
        for ((questionId, value) in answersByQuestionId) {
            val code = codeById[questionId] ?: continue
            answersByCode[code] = coerceForExpression(value)
        }

        for (question in questions) {
            val relevant = ExpressionEvaluator.isRelevant(question.relevanceExpression, answersByCode)
            if (!relevant) continue

            val value = answersByQuestionId[question.id]

            if (question.isRequired && value.isNullOrEmpty()) {
                issues.add(ValidationIssue(question.code, "This field is required."))
                continue
            }
            if (value.isNullOrEmpty()) continue

            when (question.type) {
                "INTEGER", "DECIMAL" -> {
                    val numeric = value.toDoubleOrNull()
                    if (numeric == null) {
                        issues.add(ValidationIssue(question.code, "Must be a number."))
                    } else {
                        question.minValue?.let { if (numeric < it) issues.add(ValidationIssue(question.code, "Must be at least $it.")) }
                        question.maxValue?.let { if (numeric > it) issues.add(ValidationIssue(question.code, "Must be at most $it.")) }
                    }
                }
                "SHORT_TEXT", "LONG_TEXT" -> {
                    question.minLength?.let { if (value.length < it) issues.add(ValidationIssue(question.code, "Must be at least $it characters.")) }
                    question.maxLength?.let { if (value.length > it) issues.add(ValidationIssue(question.code, "Must be at most $it characters.")) }
                    question.regexPattern?.let {
                        if (!Regex(it).containsMatchIn(value)) {
                            issues.add(ValidationIssue(question.code, "Does not match the required format."))
                        }
                    }
                }
                else -> Unit
            }
        }
        return issues
    }

    private fun coerceForExpression(value: String?): Any? {
        if (value == null) return null
        return value.toDoubleOrNull() ?: value
    }
}
