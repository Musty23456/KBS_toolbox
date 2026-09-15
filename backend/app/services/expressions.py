"""
A small, deliberately restricted expression evaluator used for:
- relevance_expression (skip logic / conditional visibility)
- calculation_expression (calculated fields)

Survey authors write expressions like:
    gender == 'FEMALE'
    age_years >= 18 and age_years < 65
    household_size * 12

Expressions reference other questions in the same survey by their `code`.
We deliberately do NOT use Python's eval() on raw survey-author input.
Instead we parse a safe AST subset (comparisons, boolean ops, arithmetic,
literals and variable names only) and reject anything else — no function
calls, no attribute access, no imports, no comprehensions.
"""
import ast
import operator
from typing import Any, Dict

_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
}

_ALLOWED_COMPARES = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda a, b: a in b,
    ast.NotIn: lambda a, b: a not in b,
}

_ALLOWED_BOOLOPS = {
    ast.And: all,
    ast.Or: any,
}


class ExpressionError(ValueError):
    pass


def _eval_node(node: ast.AST, variables: Dict[str, Any]) -> Any:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body, variables)
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        if node.id not in variables:
            # Unanswered / not-yet-visible questions evaluate to None rather
            # than raising, so relevance chains degrade gracefully.
            return None
        return variables[node.id]
    if isinstance(node, ast.BoolOp):
        op = _ALLOWED_BOOLOPS.get(type(node.op))
        if op is None:
            raise ExpressionError("Unsupported boolean operator")
        values = [bool(_eval_node(v, variables)) for v in node.values]
        return op(values)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not bool(_eval_node(node.operand, variables))
    if isinstance(node, ast.BinOp):
        op = _ALLOWED_BINOPS.get(type(node.op))
        if op is None:
            raise ExpressionError("Unsupported arithmetic operator")
        left = _eval_node(node.left, variables)
        right = _eval_node(node.right, variables)
        if left is None or right is None:
            return None
        return op(left, right)
    if isinstance(node, ast.Compare):
        left = _eval_node(node.left, variables)
        for op_node, comparator in zip(node.ops, node.comparators):
            op = _ALLOWED_COMPARES.get(type(op_node))
            if op is None:
                raise ExpressionError("Unsupported comparison operator")
            right = _eval_node(comparator, variables)
            if left is None or right is None:
                return False
            if not op(left, right):
                return False
            left = right
        return True
    if isinstance(node, ast.List):
        return [_eval_node(el, variables) for el in node.elts]
    raise ExpressionError(f"Unsupported expression element: {type(node).__name__}")


def evaluate_expression(expression: str, variables: Dict[str, Any]) -> Any:
    """
    Parses and evaluates a restricted expression string. Returns None if the
    expression is empty. Raises ExpressionError for disallowed syntax so
    survey authors get clear feedback in the form builder instead of a
    silent server error.
    """
    if not expression or not expression.strip():
        return None
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ExpressionError(f"Invalid expression syntax: {exc}") from exc
    return _eval_node(tree, variables)


def is_relevant(expression: str | None, answers: Dict[str, Any]) -> bool:
    if not expression:
        return True
    try:
        result = evaluate_expression(expression, answers)
    except ExpressionError:
        # A broken relevance expression should never hide/crash the whole
        # form — fail open and show the question.
        return True
    return bool(result)
