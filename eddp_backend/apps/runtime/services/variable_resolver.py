from __future__ import annotations

import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any

from dateutil import parser as date_parser
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

from apps.common.choices import DataTypeChoices, SourceTypeChoices
from apps.common.exceptions import ResourceNotFoundException, ValidationException
from apps.common.validators import validate_json
from apps.variables.models import Variable, VariableGroup

from ..repositories import RuntimeEngineRepository
from .expression import evaluate_safe_expression

_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.]+)\s*\}\}")


class VariableResolverService:
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
    def _split_source_reference(source_reference: str) -> tuple[str, str]:
        if not source_reference:
            return "", ""
        if ":" not in source_reference:
            return "", source_reference
        prefix, _, reference_path = source_reference.partition(":")
        normalized_prefix = prefix.strip().lower()
        if normalized_prefix in {"payload", "database", "db", "connector", "computed", "expr", "expression"}:
            return normalized_prefix, reference_path.strip()
        return "", source_reference

    @staticmethod
    def _get_by_path(data: Any, path: str) -> Any:
        if path is None or path == "":
            return data

        current_value = data
        for token in path.split("."):
            if current_value is None:
                return None
            if isinstance(current_value, dict):
                current_value = current_value.get(token)
                continue
            if isinstance(current_value, list):
                try:
                    index = int(token)
                except ValueError:
                    return None
                if index < 0 or index >= len(current_value):
                    return None
                current_value = current_value[index]
                continue
            return None
        return current_value

    def _lookup_token(
        self,
        token: str,
        *,
        runtime_payload: dict[str, Any],
        database_values: dict[str, Any],
        connector_values: dict[str, Any],
        computed_values: dict[str, Any],
        resolved_variables: dict[str, Any],
    ) -> Any:
        prefix, path = self._split_source_reference(token)

        if prefix in {"payload"}:
            return self._get_by_path(runtime_payload, path)
        if prefix in {"database", "db"}:
            return self._get_by_path(database_values, path)
        if prefix == "connector":
            return self._get_by_path(connector_values, path)
        if prefix == "computed":
            return self._get_by_path(computed_values, path)

        if token.startswith("variables."):
            return self._get_by_path(resolved_variables, token.split("variables.", 1)[1])
        if token.startswith("payload."):
            return self._get_by_path(runtime_payload, token.split("payload.", 1)[1])
        if token.startswith("database."):
            return self._get_by_path(database_values, token.split("database.", 1)[1])
        if token.startswith("connector."):
            return self._get_by_path(connector_values, token.split("connector.", 1)[1])

        if token in resolved_variables:
            return resolved_variables[token]

        payload_value = self._get_by_path(runtime_payload, token)
        if payload_value is not None:
            return payload_value

        database_value = self._get_by_path(database_values, token)
        if database_value is not None:
            return database_value

        return self._get_by_path(computed_values, token)

    def _resolve_nested(
        self,
        value: Any,
        *,
        runtime_payload: dict[str, Any],
        database_values: dict[str, Any],
        connector_values: dict[str, Any],
        computed_values: dict[str, Any],
        resolved_variables: dict[str, Any],
        max_depth: int = 8,
    ) -> Any:
        if max_depth <= 0:
            raise ValidationException(detail="Nested variable resolution exceeded recursion depth.")

        if isinstance(value, dict):
            return {
                key: self._resolve_nested(
                    item,
                    runtime_payload=runtime_payload,
                    database_values=database_values,
                    connector_values=connector_values,
                    computed_values=computed_values,
                    resolved_variables=resolved_variables,
                    max_depth=max_depth - 1,
                )
                for key, item in value.items()
            }

        if isinstance(value, list):
            return [
                self._resolve_nested(
                    item,
                    runtime_payload=runtime_payload,
                    database_values=database_values,
                    connector_values=connector_values,
                    computed_values=computed_values,
                    resolved_variables=resolved_variables,
                    max_depth=max_depth - 1,
                )
                for item in value
            ]

        if not isinstance(value, str):
            return value

        full_match = _PLACEHOLDER_PATTERN.fullmatch(value.strip())
        if full_match:
            token_value = self._lookup_token(
                full_match.group(1),
                runtime_payload=runtime_payload,
                database_values=database_values,
                connector_values=connector_values,
                computed_values=computed_values,
                resolved_variables=resolved_variables,
            )
            if token_value is None:
                return value
            return self._resolve_nested(
                token_value,
                runtime_payload=runtime_payload,
                database_values=database_values,
                connector_values=connector_values,
                computed_values=computed_values,
                resolved_variables=resolved_variables,
                max_depth=max_depth - 1,
            )

        def replace_token(match: re.Match[str]) -> str:
            token = match.group(1)
            token_value = self._lookup_token(
                token,
                runtime_payload=runtime_payload,
                database_values=database_values,
                connector_values=connector_values,
                computed_values=computed_values,
                resolved_variables=resolved_variables,
            )
            return "" if token_value is None else str(token_value)

        replaced = _PLACEHOLDER_PATTERN.sub(replace_token, value)
        if replaced != value:
            return self._resolve_nested(
                replaced,
                runtime_payload=runtime_payload,
                database_values=database_values,
                connector_values=connector_values,
                computed_values=computed_values,
                resolved_variables=resolved_variables,
                max_depth=max_depth - 1,
            )
        return replaced

    @staticmethod
    def _parse_default_value(raw_value: str, data_type: str) -> Any:
        normalized = (raw_value or "").strip()
        if normalized == "":
            return None

        if data_type == DataTypeChoices.JSON:
            try:
                return json.loads(normalized)
            except json.JSONDecodeError:
                return {"value": normalized}

        if data_type == DataTypeChoices.INTEGER:
            try:
                return int(normalized)
            except ValueError as exc:
                raise ValidationException(detail=f"Invalid integer default value: {normalized}") from exc

        if data_type == DataTypeChoices.DECIMAL:
            try:
                return str(Decimal(normalized))
            except InvalidOperation as exc:
                raise ValidationException(detail=f"Invalid decimal default value: {normalized}") from exc

        if data_type == DataTypeChoices.BOOLEAN:
            lowered = normalized.lower()
            if lowered in {"true", "1", "yes", "y"}:
                return True
            if lowered in {"false", "0", "no", "n"}:
                return False
            raise ValidationException(detail=f"Invalid boolean default value: {normalized}")

        if data_type in {DataTypeChoices.DATE, DataTypeChoices.DATETIME}:
            try:
                parsed = date_parser.parse(normalized)
                if data_type == DataTypeChoices.DATE:
                    return parsed.date().isoformat()
                return parsed.isoformat()
            except Exception as exc:
                raise ValidationException(detail=f"Invalid date default value: {normalized}") from exc

        return normalized

    @staticmethod
    def _cast_to_data_type(value: Any, data_type: str) -> Any:
        if value is None:
            return None

        if data_type == DataTypeChoices.STRING:
            return str(value)

        if data_type == DataTypeChoices.INTEGER:
            try:
                return int(value)
            except (TypeError, ValueError) as exc:
                raise ValidationException(detail=f"Cannot cast value '{value}' to integer.") from exc

        if data_type == DataTypeChoices.DECIMAL:
            try:
                return str(Decimal(str(value)))
            except (InvalidOperation, TypeError, ValueError) as exc:
                raise ValidationException(detail=f"Cannot cast value '{value}' to decimal.") from exc

        if data_type == DataTypeChoices.BOOLEAN:
            if isinstance(value, bool):
                return value
            normalized = str(value).strip().lower()
            if normalized in {"true", "1", "yes", "y"}:
                return True
            if normalized in {"false", "0", "no", "n"}:
                return False
            raise ValidationException(detail=f"Cannot cast value '{value}' to boolean.")

        if data_type == DataTypeChoices.DATE:
            try:
                parsed = date_parser.parse(str(value))
                return parsed.date().isoformat()
            except Exception as exc:
                raise ValidationException(detail=f"Cannot cast value '{value}' to date.") from exc

        if data_type == DataTypeChoices.DATETIME:
            try:
                parsed = date_parser.parse(str(value))
                return parsed.isoformat()
            except Exception as exc:
                raise ValidationException(detail=f"Cannot cast value '{value}' to datetime.") from exc

        if data_type == DataTypeChoices.JSON:
            if isinstance(value, (dict, list)):
                return value
            try:
                return json.loads(str(value))
            except json.JSONDecodeError as exc:
                raise ValidationException(detail=f"Cannot cast value '{value}' to JSON.") from exc

        return value

    def _build_expression_context(
        self,
        *,
        runtime_payload: dict[str, Any],
        database_values: dict[str, Any],
        connector_values: dict[str, Any],
        computed_values: dict[str, Any],
        resolved_variables: dict[str, Any],
    ) -> dict[str, Any]:
        context: dict[str, Any] = {
            "payload": runtime_payload,
            "database": database_values,
            "connector": connector_values,
            "computed": computed_values,
            "variables": resolved_variables,
        }
        context.update(resolved_variables)
        return context

    def load_variable_group(self, variable_group_code: str) -> tuple[VariableGroup, list[Variable]]:
        if not variable_group_code:
            raise ValidationException(detail="variable_group_code is required.")

        variable_group = self.repository.get_variable_group_by_code(variable_group_code)
        if variable_group is None:
            raise ResourceNotFoundException(detail=f"Variable group '{variable_group_code}' not found.")

        variables = list(self.repository.get_variables_by_group(variable_group))
        return variable_group, variables

    def resolve_variable(
        self,
        *,
        variable: Variable,
        runtime_payload: dict[str, Any],
        database_values: dict[str, Any],
        connector_values: dict[str, Any],
        computed_values: dict[str, Any],
        resolved_variables: dict[str, Any],
    ) -> Any:
        if variable.name in computed_values:
            value = computed_values[variable.name]
        else:
            source_reference = (variable.source_reference or variable.name or "").strip()
            source_prefix, source_path = self._split_source_reference(source_reference)

            value = None
            if source_prefix == "payload":
                value = self._get_by_path(runtime_payload, source_path)
            elif source_prefix in {"database", "db"}:
                value = self._get_by_path(database_values, source_path)
            elif source_prefix == "connector":
                value = self._get_by_path(connector_values, source_path)
            elif source_prefix == "computed":
                value = self._get_by_path(computed_values, source_path)
            elif source_prefix in {"expr", "expression"}:
                expression_context = self._build_expression_context(
                    runtime_payload=runtime_payload,
                    database_values=database_values,
                    connector_values=connector_values,
                    computed_values=computed_values,
                    resolved_variables=resolved_variables,
                )
                value = evaluate_safe_expression(source_path, expression_context)
            elif variable.source_type == SourceTypeChoices.INPUT:
                value = self._get_by_path(runtime_payload, source_reference or variable.name)
            elif variable.source_type == SourceTypeChoices.CONNECTOR:
                value = self._get_by_path(connector_values, source_reference or variable.name)
            elif variable.source_type == SourceTypeChoices.RULE:
                value = self._get_by_path(computed_values, source_reference or variable.name)
            elif variable.source_type == SourceTypeChoices.DERIVED:
                expression = source_reference or (variable.default_value or "")
                expression_context = self._build_expression_context(
                    runtime_payload=runtime_payload,
                    database_values=database_values,
                    connector_values=connector_values,
                    computed_values=computed_values,
                    resolved_variables=resolved_variables,
                )
                value = evaluate_safe_expression(expression, expression_context)
            elif variable.source_type == SourceTypeChoices.STATIC:
                value = self._parse_default_value(variable.default_value, variable.data_type)

            if value is None:
                fallback_reference = source_reference or variable.name
                value = self._get_by_path(database_values, fallback_reference)

            if value is None:
                value = self._parse_default_value(variable.default_value, variable.data_type)

        value = self._resolve_nested(
            value,
            runtime_payload=runtime_payload,
            database_values=database_values,
            connector_values=connector_values,
            computed_values=computed_values,
            resolved_variables=resolved_variables,
        )

        return self._cast_to_data_type(value, variable.data_type)

    def validate_required_variables(
        self,
        variables: list[Variable],
        resolved_variables: dict[str, Any],
    ) -> None:
        missing_variables = []
        for variable in variables:
            if not variable.is_required:
                continue
            value = resolved_variables.get(variable.name)
            if value is None or value == "" or value == [] or value == {}:
                missing_variables.append(variable.name)

        if missing_variables:
            raise ValidationException(
                detail="Required variables are missing.",
                errors={"missing_variables": missing_variables},
            )

    def resolve_variables(
        self,
        *,
        variable_group_code: str,
        runtime_payload: Any,
        database_values: Any = None,
        connector_values: Any = None,
        computed_values: Any = None,
    ) -> dict[str, Any]:
        payload = self._ensure_dict(runtime_payload, "runtime_payload")
        database_context = self._ensure_dict(database_values, "database_values")
        connector_context = self._ensure_dict(connector_values, "connector_values")
        computed_context = self._ensure_dict(computed_values, "computed_values")

        variable_group, variables = self.load_variable_group(variable_group_code)

        execution_log: list[dict[str, Any]] = []
        self._log(
            execution_log,
            stage="VARIABLE_RESOLUTION_START",
            message="Variable resolution started.",
            metadata={
                "variable_group_code": variable_group.code,
                "variable_count": len(variables),
            },
        )

        resolved_variables: dict[str, Any] = {}
        unresolved_variables = list(variables)
        max_passes = max(1, len(unresolved_variables) * 2)

        for pass_index in range(1, max_passes + 1):
            if not unresolved_variables:
                break

            self._log(
                execution_log,
                stage="VARIABLE_RESOLUTION_PASS",
                message=f"Resolution pass {pass_index} started.",
                metadata={"pending": [variable.name for variable in unresolved_variables]},
            )

            next_round: list[Variable] = []
            resolved_in_pass = 0

            for variable in unresolved_variables:
                try:
                    value = self.resolve_variable(
                        variable=variable,
                        runtime_payload=payload,
                        database_values=database_context,
                        connector_values=connector_context,
                        computed_values=computed_context,
                        resolved_variables=resolved_variables,
                    )
                    if value is None and variable.is_required:
                        next_round.append(variable)
                        self._log(
                            execution_log,
                            stage="VARIABLE_DEFERRED",
                            message="Required variable deferred to next pass.",
                            metadata={"variable": variable.name},
                        )
                        continue

                    resolved_variables[variable.name] = value
                    resolved_in_pass += 1
                    self._log(
                        execution_log,
                        stage="VARIABLE_RESOLVED",
                        message="Variable resolved successfully.",
                        metadata={"variable": variable.name, "source_type": variable.source_type},
                    )
                except ValidationException as exc:
                    detail_text = str(exc.detail)
                    if variable.source_type == SourceTypeChoices.DERIVED and "Unknown name" in detail_text:
                        next_round.append(variable)
                        self._log(
                            execution_log,
                            stage="VARIABLE_DEFERRED",
                            message="Computed variable deferred due to unresolved dependency.",
                            metadata={"variable": variable.name},
                        )
                        continue
                    raise

            unresolved_variables = next_round
            if unresolved_variables and resolved_in_pass == 0:
                break

        if unresolved_variables:
            unresolved_names = [variable.name for variable in unresolved_variables]
            raise ValidationException(
                detail="Unable to resolve all variables due to unresolved dependencies.",
                errors={"unresolved_variables": unresolved_names},
            )

        self.validate_required_variables(variables, resolved_variables)
        self._log(
            execution_log,
            stage="VARIABLE_RESOLUTION_COMPLETE",
            message="Variable resolution completed successfully.",
            metadata={"resolved_count": len(resolved_variables)},
        )

        return {
            "variable_group_code": variable_group.code,
            "variable_group_name": variable_group.name,
            "resolved_variables": resolved_variables,
            "validation_results": {
                "valid": True,
                "missing_variables": [],
            },
            "execution_log": execution_log,
        }
