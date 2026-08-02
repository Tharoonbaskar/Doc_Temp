from __future__ import annotations

import ast
import operator
from typing import Any

from apps.common.exceptions import ValidationException


_ALLOWED_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_ALLOWED_UNARY_OPS = {
    ast.Not: operator.not_,
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}

_ALLOWED_COMPARE_OPS = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
    ast.In: lambda left, right: left in right,
    ast.NotIn: lambda left, right: left not in right,
    ast.Is: lambda left, right: left is right,
    ast.IsNot: lambda left, right: left is not right,
}

_ALLOWED_FUNCTIONS = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "float": float,
    "int": int,
    "len": len,
    "max": max,
    "min": min,
    "round": round,
    "sorted": sorted,
    "str": str,
    "sum": sum,
}


class SafeExpressionEvaluator(ast.NodeVisitor):
    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context

    def evaluate(self, expression: str) -> Any:
        try:
            parsed = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise ValidationException(detail=f"Invalid expression syntax: {exc.msg}") from exc
        return self.visit(parsed.body)

    def visit_Constant(self, node: ast.Constant) -> Any:
        return node.value

    def visit_Name(self, node: ast.Name) -> Any:
        if node.id in self.context:
            return self.context[node.id]
        if node.id in _ALLOWED_FUNCTIONS:
            return _ALLOWED_FUNCTIONS[node.id]
        if node.id in {"True", "False", "None"}:
            return {"True": True, "False": False, "None": None}[node.id]
        raise ValidationException(detail=f"Unknown name in expression: {node.id}")

    def visit_List(self, node: ast.List) -> list[Any]:
        return [self.visit(item) for item in node.elts]

    def visit_Tuple(self, node: ast.Tuple) -> tuple[Any, ...]:
        return tuple(self.visit(item) for item in node.elts)

    def visit_Dict(self, node: ast.Dict) -> dict[Any, Any]:
        return {
            self.visit(key): self.visit(value)
            for key, value in zip(node.keys, node.values)
        }

    def visit_BoolOp(self, node: ast.BoolOp) -> Any:
        values = [self.visit(value) for value in node.values]
        if isinstance(node.op, ast.And):
            return all(values)
        if isinstance(node.op, ast.Or):
            return any(values)
        raise ValidationException(detail="Unsupported boolean operator.")

    def visit_BinOp(self, node: ast.BinOp) -> Any:
        operator_fn = _ALLOWED_BIN_OPS.get(type(node.op))
        if operator_fn is None:
            raise ValidationException(detail="Unsupported binary operator.")
        return operator_fn(self.visit(node.left), self.visit(node.right))

    def visit_UnaryOp(self, node: ast.UnaryOp) -> Any:
        operator_fn = _ALLOWED_UNARY_OPS.get(type(node.op))
        if operator_fn is None:
            raise ValidationException(detail="Unsupported unary operator.")
        return operator_fn(self.visit(node.operand))

    def visit_Compare(self, node: ast.Compare) -> bool:
        left_value = self.visit(node.left)
        for op, comparator in zip(node.ops, node.comparators):
            right_value = self.visit(comparator)
            comparator_fn = _ALLOWED_COMPARE_OPS.get(type(op))
            if comparator_fn is None:
                raise ValidationException(detail="Unsupported comparison operator.")
            if not comparator_fn(left_value, right_value):
                return False
            left_value = right_value
        return True

    def visit_IfExp(self, node: ast.IfExp) -> Any:
        condition = self.visit(node.test)
        return self.visit(node.body) if condition else self.visit(node.orelse)

    def visit_Subscript(self, node: ast.Subscript) -> Any:
        value = self.visit(node.value)
        index = self.visit(node.slice)
        try:
            return value[index]
        except Exception as exc:
            raise ValidationException(detail="Subscript lookup failed.") from exc

    def visit_Slice(self, node: ast.Slice) -> slice:
        lower = self.visit(node.lower) if node.lower is not None else None
        upper = self.visit(node.upper) if node.upper is not None else None
        step = self.visit(node.step) if node.step is not None else None
        return slice(lower, upper, step)

    def visit_Attribute(self, node: ast.Attribute) -> Any:
        value = self.visit(node.value)
        if isinstance(value, dict):
            return value.get(node.attr)
        if hasattr(value, node.attr):
            return getattr(value, node.attr)
        raise ValidationException(detail=f"Attribute '{node.attr}' not found.")

    def visit_Call(self, node: ast.Call) -> Any:
        if not isinstance(node.func, ast.Name):
            raise ValidationException(detail="Only direct function calls are allowed.")
        function_name = node.func.id
        function = _ALLOWED_FUNCTIONS.get(function_name)
        if function is None:
            raise ValidationException(detail=f"Function '{function_name}' is not allowed.")
        args = [self.visit(arg) for arg in node.args]
        kwargs = {kw.arg: self.visit(kw.value) for kw in node.keywords}
        return function(*args, **kwargs)

    def generic_visit(self, node: ast.AST):
        raise ValidationException(detail=f"Unsupported expression node: {type(node).__name__}")


def evaluate_safe_expression(expression: str, context: dict[str, Any]) -> Any:
    evaluator = SafeExpressionEvaluator(context=context)
    return evaluator.evaluate(expression)
