from __future__ import annotations

import json
from time import perf_counter
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

from apps.common.choices import RuleTypeChoices
from apps.common.exceptions import ResourceNotFoundException, ValidationException
from apps.common.validators import validate_json
from apps.rules.models import Rule, RuleGroup

from ..repositories import RuntimeEngineRepository
from .expression import evaluate_safe_expression

_PHASE_ORDER = {
    "pre": 1,
    "validation": 2,
    "business": 3,
    "post": 4,
}


class RuleExecutionService:
    def __init__(self, repository: RuntimeEngineRepository | None = None) -> None:
        self.repository = repository or RuntimeEngineRepository()

    @staticmethod
    def _log(
        logs: list[dict[str, Any]],
        *,
        stage: str,
        message: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        logs.append(
            {
                "timestamp": timezone.now().isoformat(),
                "stage": stage,
                "message": message,
                "metadata": metadata or {},
            }
        )

    @staticmethod
    def _ensure_dict(value: Any, field_name: str) -> dict[str, Any]:
        if value is None:
            return {}
        try:
            parsed = validate_json(value)
        except DjangoValidationError as exc:
            raise ValidationException(detail=str(exc)) from exc
        if not isinstance(parsed, dict):
            raise ValidationException(detail=f"{field_name} must be a JSON object.")
        return parsed

    @staticmethod
    def _phase_from_rule(rule: Rule, configured_phase: str | None) -> str:
        if configured_phase:
            normalized_phase = configured_phase.strip().lower()
            if normalized_phase in _PHASE_ORDER:
                return normalized_phase

        normalized_name = (rule.name or "").strip().lower()
        normalized_description = (rule.description or "").strip().lower()

        if normalized_name.startswith(("pre_", "pre-", "pre ")) or "[pre]" in normalized_description:
            return "pre"
        if normalized_name.startswith(("post_", "post-", "post ")) or "[post]" in normalized_description:
            return "post"
        if rule.rule_type == RuleTypeChoices.VALIDATION:
            return "validation"
        return "business"

    def _parse_rule_expression(self, rule: Rule) -> dict[str, Any]:
        raw_expression = (rule.expression or "").strip()
        if not raw_expression:
            raise ValidationException(detail=f"Rule '{rule.code}' has an empty expression.")

        expression_payload: dict[str, Any] = {}
        expression_text = raw_expression

        if raw_expression.startswith("{") and raw_expression.endswith("}"):
            try:
                parsed = json.loads(raw_expression)
                if isinstance(parsed, dict):
                    expression_payload = parsed
                    expression_text = str(parsed.get("expression") or "").strip()
            except json.JSONDecodeError:
                expression_payload = {}

        if not expression_text:
            raise ValidationException(detail=f"Rule '{rule.code}' expression is invalid.")

        phase = self._phase_from_rule(rule, str(expression_payload.get("phase") or ""))
        critical = bool(expression_payload.get("critical", rule.rule_type == RuleTypeChoices.VALIDATION))

        return {
            "expression": expression_text,
            "phase": phase,
            "critical": critical,
            "message": str(expression_payload.get("message") or ""),
        }

    def load_rule_group(self, rule_group_code: str) -> tuple[RuleGroup, list[Rule]]:
        if not rule_group_code:
            raise ValidationException(detail="rule_group_code is required.")

        rule_group = self.repository.get_rule_group_by_code(rule_group_code)
        if rule_group is None:
            raise ResourceNotFoundException(detail=f"Rule group '{rule_group_code}' not found.")

        rules = list(self.repository.get_rules_by_group(rule_group))
        return rule_group, rules

    @staticmethod
    def validate_rule(rule: Rule) -> None:
        if not rule.is_active:
            raise ValidationException(detail=f"Rule '{rule.code}' is inactive.")
        if not (rule.expression or "").strip():
            raise ValidationException(detail=f"Rule '{rule.code}' has no expression.")
        if rule.execution_order < 1:
            raise ValidationException(detail=f"Rule '{rule.code}' has invalid execution_order.")

    @staticmethod
    def evaluate_expression(expression: str, context: dict[str, Any]) -> Any:
        return evaluate_safe_expression(expression, context)

    @staticmethod
    def get_execution_summary(
        execution_results: list[dict[str, Any]],
        *,
        validation_results: list[dict[str, Any]],
        stopped_on_failure: bool,
    ) -> dict[str, Any]:
        total = len(execution_results)
        passed = sum(1 for item in execution_results if item.get("status") == "PASSED")
        failed = sum(1 for item in execution_results if item.get("status") == "FAILED")
        errored = sum(1 for item in execution_results if item.get("status") == "ERROR")
        validation_failed = sum(
            1 for item in validation_results if not bool(item.get("passed"))
        )

        return {
            "total_rules": total,
            "passed_rules": passed,
            "failed_rules": failed,
            "errored_rules": errored,
            "validation_failed": validation_failed,
            "stopped_on_critical_failure": stopped_on_failure,
            "success": failed == 0 and errored == 0,
        }

    def execute_rules(
        self,
        *,
        rule_group_code: str,
        runtime_context: Any,
        stop_on_critical_failure: bool = True,
    ) -> dict[str, Any]:
        normalized_context = self._ensure_dict(runtime_context, "runtime_context")
        rule_group, rules = self.load_rule_group(rule_group_code)

        execution_log: list[dict[str, Any]] = []
        self._log(
            execution_log,
            stage="RULE_EXECUTION_START",
            message="Rule execution started.",
            metadata={
                "rule_group_code": rule_group.code,
                "rule_count": len(rules),
            },
        )

        prepared_rules: list[tuple[Rule, dict[str, Any]]] = []
        for rule in rules:
            self.validate_rule(rule)
            prepared_rules.append((rule, self._parse_rule_expression(rule)))

        prepared_rules.sort(
            key=lambda item: (
                _PHASE_ORDER.get(item[1]["phase"], 99),
                item[0].execution_order,
                item[0].name.lower(),
            )
        )

        evaluation_context: dict[str, Any] = dict(normalized_context)
        if "variables" not in evaluation_context and isinstance(
            normalized_context.get("resolved_variables"), dict
        ):
            evaluation_context["variables"] = normalized_context["resolved_variables"]
        if isinstance(evaluation_context.get("variables"), dict):
            evaluation_context.update(evaluation_context["variables"])

        executed_rules: list[dict[str, Any]] = []
        validation_items: list[dict[str, Any]] = []
        stopped_on_failure = False

        for rule, parsed_expression in prepared_rules:
            phase = parsed_expression["phase"]
            critical = bool(parsed_expression["critical"])
            expression = parsed_expression["expression"]
            started_at = perf_counter()

            self._log(
                execution_log,
                stage="RULE_EXECUTING",
                message="Executing rule.",
                metadata={
                    "rule_code": rule.code,
                    "rule_name": rule.name,
                    "phase": phase,
                    "execution_order": rule.execution_order,
                },
            )

            result_value: Any = None
            status = "PASSED"
            passed = True
            message = parsed_expression["message"]
            error_message = ""

            try:
                result_value = self.evaluate_expression(expression, evaluation_context)
                if isinstance(result_value, bool):
                    passed = result_value
                else:
                    passed = bool(result_value)
                status = "PASSED" if passed else "FAILED"
                if not message:
                    message = "Rule evaluated successfully." if passed else "Rule evaluated to false."

                if isinstance(result_value, dict):
                    evaluation_context.update(result_value)
                    if isinstance(result_value.get("variables"), dict):
                        current_variables = evaluation_context.get("variables", {})
                        if not isinstance(current_variables, dict):
                            current_variables = {}
                        current_variables.update(result_value["variables"])
                        evaluation_context["variables"] = current_variables
                        evaluation_context.update(current_variables)
            except Exception as exc:
                passed = False
                status = "ERROR"
                error_message = str(exc)
                if not message:
                    message = "Rule evaluation failed."

            duration_ms = round((perf_counter() - started_at) * 1000, 3)
            execution_result = {
                "rule_id": str(rule.id),
                "rule_code": rule.code,
                "rule_name": rule.name,
                "rule_type": rule.rule_type,
                "phase": phase,
                "critical": critical,
                "execution_order": rule.execution_order,
                "status": status,
                "passed": passed,
                "result": result_value,
                "message": message,
                "error": error_message,
                "duration_ms": duration_ms,
            }
            executed_rules.append(execution_result)

            self._log(
                execution_log,
                stage="RULE_EXECUTED",
                message="Rule execution completed.",
                metadata={
                    "rule_code": rule.code,
                    "status": status,
                    "passed": passed,
                    "duration_ms": duration_ms,
                },
            )

            if phase == "validation":
                validation_items.append(
                    {
                        "rule_code": rule.code,
                        "rule_name": rule.name,
                        "passed": passed,
                        "critical": critical,
                        "message": message,
                    }
                )
                if stop_on_critical_failure and critical and not passed:
                    stopped_on_failure = True
                    self._log(
                        execution_log,
                        stage="RULE_EXECUTION_STOPPED",
                        message="Execution stopped on critical validation failure.",
                        metadata={"rule_code": rule.code},
                    )
                    break

        summary = self.get_execution_summary(
            executed_rules,
            validation_results=validation_items,
            stopped_on_failure=stopped_on_failure,
        )

        validation_results = {
            "valid": all(item.get("passed", False) for item in validation_items),
            "items": validation_items,
            "failed_count": sum(1 for item in validation_items if not item.get("passed", False)),
            "stopped_on_critical_failure": stopped_on_failure,
        }

        self._log(
            execution_log,
            stage="RULE_EXECUTION_COMPLETE",
            message="Rule execution completed.",
            metadata=summary,
        )

        return {
            "rule_group_code": rule_group.code,
            "rule_group_name": rule_group.name,
            "executed_rules": executed_rules,
            "validation_results": validation_results,
            "execution_log": execution_log,
            "summary": summary,
            "runtime_context": evaluation_context,
        }
