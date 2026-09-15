import pytest

from app.services.expressions import ExpressionError, evaluate_expression, is_relevant


def test_simple_equality():
    assert evaluate_expression("gender == 'FEMALE'", {"gender": "FEMALE"}) is True
    assert evaluate_expression("gender == 'FEMALE'", {"gender": "MALE"}) is False


def test_boolean_and_range():
    vars_ = {"age_years": 25}
    assert evaluate_expression("age_years >= 18 and age_years < 65", vars_) is True
    vars_ = {"age_years": 70}
    assert evaluate_expression("age_years >= 18 and age_years < 65", vars_) is False


def test_arithmetic_calculation():
    assert evaluate_expression("household_size * 12", {"household_size": 4}) == 48


def test_missing_variable_is_none_not_error():
    assert evaluate_expression("gender == 'FEMALE'", {}) is False


def test_disallowed_syntax_rejected():
    with pytest.raises(ExpressionError):
        evaluate_expression("__import__('os').system('rm -rf /')", {})


def test_disallowed_function_call_rejected():
    with pytest.raises(ExpressionError):
        evaluate_expression("len(x)", {"x": "abc"})


def test_is_relevant_defaults_true_when_empty():
    assert is_relevant(None, {}) is True
    assert is_relevant("", {}) is True


def test_is_relevant_fails_open_on_broken_expression():
    # A malformed expression should never crash form rendering — it should
    # fail open (question stays visible) so a bad rule can't hide critical
    # questions from the field.
    assert is_relevant("this is not valid python (((", {}) is True
