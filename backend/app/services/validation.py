import re
from typing import Dict, List

from app.models.question import Question, QuestionType
from app.services.expressions import is_relevant


class ValidationIssue:
    def __init__(self, question_code: str, message: str):
        self.question_code = question_code
        self.message = message

    def __repr__(self):
        return f"{self.question_code}: {self.message}"


def validate_submission_answers(
    questions: List[Question], answers_by_question_id: Dict[str, str]
) -> List[ValidationIssue]:
    """
    Re-validates a submission server-side (required fields, ranges, regex,
    relevance) rather than trusting the Android client. Field enumerators
    can't bypass rules just by editing the offline app's local database.
    """
    issues: List[ValidationIssue] = []

    # answers keyed by question code for relevance-expression evaluation
    answers_by_code = {}
    code_by_id = {q.id: q.code for q in questions}
    for q_id, value in answers_by_question_id.items():
        code = code_by_id.get(q_id)
        if code:
            answers_by_code[code] = _coerce_for_expression(value)

    for question in questions:
        value = answers_by_question_id.get(question.id)
        relevant = is_relevant(question.relevance_expression, answers_by_code)

        if not relevant:
            continue  # hidden questions are not validated

        if question.is_required and (value is None or value == ""):
            issues.append(ValidationIssue(question.code, "This field is required."))
            continue

        if value in (None, ""):
            continue

        if question.type in (QuestionType.INTEGER, QuestionType.DECIMAL):
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                issues.append(ValidationIssue(question.code, "Must be a number."))
                continue
            if question.min_value is not None and numeric < question.min_value:
                issues.append(ValidationIssue(question.code, f"Must be at least {question.min_value}."))
            if question.max_value is not None and numeric > question.max_value:
                issues.append(ValidationIssue(question.code, f"Must be at most {question.max_value}."))

        if question.type in (QuestionType.SHORT_TEXT, QuestionType.LONG_TEXT):
            if question.min_length is not None and len(value) < question.min_length:
                issues.append(ValidationIssue(question.code, f"Must be at least {question.min_length} characters."))
            if question.max_length is not None and len(value) > question.max_length:
                issues.append(ValidationIssue(question.code, f"Must be at most {question.max_length} characters."))
            if question.regex_pattern and not re.match(question.regex_pattern, value):
                issues.append(ValidationIssue(question.code, "Does not match the required format."))

    return issues


def _coerce_for_expression(value):
    if value is None:
        return None
    try:
        if "." in value:
            return float(value)
        return int(value)
    except (TypeError, ValueError):
        return value
