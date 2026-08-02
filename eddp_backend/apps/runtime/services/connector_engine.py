from __future__ import annotations

import base64
import json
import re
import uuid
import xml.etree.ElementTree as ET
from time import perf_counter
from typing import Any
from urllib.parse import urljoin

import requests
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import connections
from django.utils import timezone

from apps.common.choices import AuthenticationTypeChoices, ConnectorTypeChoices
from apps.common.exceptions import (
    ExternalServiceException,
    ResourceNotFoundException,
    ValidationException,
)
from apps.common.validators import validate_json
from apps.connectors.models import Connector, ConnectorConfiguration

from ..repositories import RuntimeEngineRepository

_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.\[\]]+)\s*\}\}")


class ConnectorExecutionService:
    def __init__(
        self,
        repository: RuntimeEngineRepository | None = None,
        session: requests.Session | None = None,
    ) -> None:
        self.repository = repository or RuntimeEngineRepository()
        self.session = session or requests.Session()

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
    def _split_reference(path: str) -> list[str]:
        normalized = path.replace("]", "").replace("[", ".")
        return [token for token in normalized.split(".") if token]

    @classmethod
    def _get_by_path(cls, data: Any, path: str) -> Any:
        if not path:
            return data
        current_value = data
        for token in cls._split_reference(path):
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

    def _resolve_placeholders(self, value: str, context: dict[str, Any]) -> str:
        if not isinstance(value, str) or "{{" not in value:
            return value

        def replace(match: re.Match[str]) -> str:
            reference = match.group(1)
            resolved = self._get_by_path(context, reference)
            return "" if resolved is None else str(resolved)

        return _PLACEHOLDER_PATTERN.sub(replace, value)

    @staticmethod
    def _resolve_endpoint(base_url: str, endpoint: str) -> str:
        cleaned_endpoint = (endpoint or "").strip()
        cleaned_base = (base_url or "").strip()
        if not cleaned_endpoint:
            return cleaned_base
        if cleaned_endpoint.startswith("http://") or cleaned_endpoint.startswith("https://"):
            return cleaned_endpoint
        if not cleaned_base:
            return cleaned_endpoint
        return urljoin(cleaned_base.rstrip("/") + "/", cleaned_endpoint.lstrip("/"))

    def _load_connector(self, connector_code: str) -> tuple[Connector, ConnectorConfiguration | None]:
        if not connector_code:
            raise ValidationException(detail="connector_code is required.")
        connector = self.repository.get_connector_by_code(connector_code)
        if connector is None:
            raise ResourceNotFoundException(detail=f"Connector '{connector_code}' not found.")
        configuration = self.repository.get_connector_configuration(connector)
        return connector, configuration

    @staticmethod
    def _configuration_json(configuration: ConnectorConfiguration | None) -> dict[str, Any]:
        if not configuration:
            return {}
        config_value = configuration.configuration_json
        return config_value if isinstance(config_value, dict) else {}

    @staticmethod
    def _headers_json(configuration: ConnectorConfiguration | None) -> dict[str, str]:
        if not configuration:
            return {}
        headers_value = configuration.headers_json
        if not isinstance(headers_value, dict):
            return {}
        return {str(key): str(value) for key, value in headers_value.items()}

    @staticmethod
    def _authentication_json(configuration: ConnectorConfiguration | None) -> dict[str, Any]:
        if not configuration:
            return {}
        auth_value = configuration.authentication_json
        return auth_value if isinstance(auth_value, dict) else {}

    def _build_auth_headers(
        self,
        connector: Connector,
        configuration: ConnectorConfiguration | None,
    ) -> dict[str, str]:
        if not configuration:
            return {}

        auth_type = configuration.authentication_type
        auth_data = self._authentication_json(configuration)

        if auth_type == AuthenticationTypeChoices.BASIC:
            username = str(auth_data.get("username") or connector.username or "")
            password = str(auth_data.get("password") or connector.password or "")
            encoded = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")
            return {"Authorization": f"Basic {encoded}"}

        if auth_type == AuthenticationTypeChoices.API_KEY:
            key_name = str(auth_data.get("key_name") or "X-API-Key")
            key_value = str(
                auth_data.get("api_key")
                or auth_data.get("key")
                or auth_data.get("value")
                or ""
            )
            if key_value:
                return {key_name: key_value}
            return {}

        if auth_type in {
            AuthenticationTypeChoices.BEARER_TOKEN,
            AuthenticationTypeChoices.OAUTH2,
        }:
            token = str(
                auth_data.get("token")
                or auth_data.get("access_token")
                or auth_data.get("bearer_token")
                or ""
            )
            if token:
                return {"Authorization": f"Bearer {token}"}
            return {}

        return {}

    def _resolve_execution_mode(
        self,
        *,
        connector: Connector,
        configuration: ConnectorConfiguration | None,
        operation: str,
        payload: dict[str, Any],
    ) -> str:
        config_json = self._configuration_json(configuration)
        normalized_operation = (operation or "").strip().lower()

        explicit_mode = (
            payload.get("execution_mode")
            or payload.get("mode")
            or config_json.get("execution_mode")
            or normalized_operation
            or ""
        )
        normalized_mode = str(explicit_mode).strip().lower()

        if normalized_mode in {"stored_procedure", "storedprocedure", "sp"}:
            return "stored_procedure"
        if normalized_mode in {"database", "sql"}:
            return "database"
        if normalized_mode in {"rest", "rest_api", "http", "https", "api", "webhook"}:
            return "rest"
        if normalized_mode in {"soap", "soap_api"}:
            return "soap"
        if normalized_mode in {"queue", "message_queue", "event_queue"}:
            return "queue"

        protocol = str(payload.get("protocol") or config_json.get("protocol") or "").strip().lower()
        if protocol == "soap":
            return "soap"
        if protocol in {"http", "https", "rest"}:
            return "rest"

        if connector.connector_type == ConnectorTypeChoices.DATABASE:
            return "database"
        if connector.connector_type == ConnectorTypeChoices.API:
            return "rest"
        if connector.connector_type == ConnectorTypeChoices.QUEUE:
            return "queue"
        if connector.connector_type == ConnectorTypeChoices.WEBHOOK:
            return "rest"

        return "rest"

    @staticmethod
    def _fetch_cursor_rows(cursor) -> list[dict[str, Any]]:
        if cursor.description is None:
            return []
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]

    def _xml_to_dict(self, element: ET.Element) -> Any:
        children = list(element)
        if not children:
            return (element.text or "").strip()

        grouped: dict[str, Any] = {}
        for child in children:
            child_value = self._xml_to_dict(child)
            if child.tag in grouped:
                existing = grouped[child.tag]
                if isinstance(existing, list):
                    existing.append(child_value)
                else:
                    grouped[child.tag] = [existing, child_value]
            else:
                grouped[child.tag] = child_value
        return grouped

    def _validate_connection_internal(
        self,
        *,
        connector: Connector,
        configuration: ConnectorConfiguration | None,
        execution_mode: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        config_json = self._configuration_json(configuration)
        timeout = int(payload.get("timeout") or connector.timeout)

        if execution_mode in {"database", "stored_procedure"}:
            db_alias = str(payload.get("database_alias") or config_json.get("database_alias") or "default")
            started_at = perf_counter()
            with connections[db_alias].cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return {
                "valid": True,
                "mode": execution_mode,
                "database_alias": db_alias,
                "duration_ms": round((perf_counter() - started_at) * 1000, 3),
            }

        if execution_mode == "rest":
            health_endpoint = str(
                payload.get("health_endpoint")
                or config_json.get("health_endpoint")
                or payload.get("endpoint")
                or config_json.get("endpoint")
                or connector.api_base_url
                or ""
            )
            url = self._resolve_endpoint(connector.api_base_url, health_endpoint)
            if not url:
                raise ValidationException(detail="REST connector endpoint is not configured.")

            method = str(payload.get("health_method") or "GET").upper()
            headers = self._headers_json(configuration)
            headers.update(self._build_auth_headers(connector, configuration))

            started_at = perf_counter()
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                timeout=timeout,
            )
            if response.status_code >= 500:
                raise ExternalServiceException(
                    detail=f"REST connector health check failed with status {response.status_code}."
                )
            return {
                "valid": True,
                "mode": "rest",
                "url": url,
                "method": method,
                "status_code": response.status_code,
                "duration_ms": round((perf_counter() - started_at) * 1000, 3),
            }

        if execution_mode == "soap":
            endpoint = str(
                payload.get("soap_endpoint")
                or config_json.get("soap_endpoint")
                or payload.get("endpoint")
                or connector.api_base_url
                or ""
            )
            url = self._resolve_endpoint(connector.api_base_url, endpoint)
            if not url:
                raise ValidationException(detail="SOAP endpoint is not configured.")

            ping_envelope = str(payload.get("ping_envelope") or config_json.get("ping_envelope") or "").strip()
            headers = self._headers_json(configuration)
            headers.update(self._build_auth_headers(connector, configuration))
            started_at = perf_counter()

            if ping_envelope:
                response = self.session.post(
                    url,
                    data=ping_envelope.encode("utf-8"),
                    headers={"Content-Type": "text/xml; charset=utf-8", **headers},
                    timeout=timeout,
                )
            else:
                response = self.session.get(url, headers=headers, timeout=timeout)

            if response.status_code >= 500:
                raise ExternalServiceException(
                    detail=f"SOAP connector health check failed with status {response.status_code}."
                )
            return {
                "valid": True,
                "mode": "soap",
                "url": url,
                "status_code": response.status_code,
                "duration_ms": round((perf_counter() - started_at) * 1000, 3),
            }

        if execution_mode == "queue":
            queue_name = str(
                payload.get("queue_name") or config_json.get("queue_name") or connector.code
            ).strip()
            if not queue_name:
                raise ValidationException(detail="Queue name is required for queue connectors.")
            return {
                "valid": True,
                "mode": "queue",
                "queue_name": queue_name,
            }

        raise ValidationException(detail=f"Unsupported execution mode '{execution_mode}'.")

    def validate_connection(
        self,
        *,
        connector_code: str,
        payload: Any = None,
        operation: str = "",
    ) -> dict[str, Any]:
        connector, configuration = self._load_connector(connector_code)
        payload_dict = self._ensure_dict(payload, "payload")
        execution_mode = self._resolve_execution_mode(
            connector=connector,
            configuration=configuration,
            operation=operation,
            payload=payload_dict,
        )

        try:
            return self._validate_connection_internal(
                connector=connector,
                configuration=configuration,
                execution_mode=execution_mode,
                payload=payload_dict,
            )
        except requests.RequestException as exc:
            raise ExternalServiceException(detail=f"Connection validation failed: {exc}") from exc

    def execute_database(
        self,
        *,
        connector: Connector,
        configuration: ConnectorConfiguration | None,
        payload: dict[str, Any],
        operation: str,
        execution_log: list[dict[str, Any]],
    ) -> dict[str, Any]:
        config_json = self._configuration_json(configuration)
        db_alias = str(payload.get("database_alias") or config_json.get("database_alias") or "default")
        is_stored_procedure = (
            (operation or "").strip().lower() in {"stored_procedure", "sp", "call"}
            or bool(payload.get("stored_procedure"))
            or bool(config_json.get("stored_procedure"))
        )

        started_at = perf_counter()
        with connections[db_alias].cursor() as cursor:
            if is_stored_procedure:
                procedure_name = str(
                    payload.get("stored_procedure")
                    or payload.get("procedure")
                    or config_json.get("stored_procedure")
                    or ""
                ).strip()
                if not procedure_name:
                    raise ValidationException(detail="stored_procedure name is required.")

                params = payload.get("params") or config_json.get("params") or []
                if not isinstance(params, (list, tuple)):
                    raise ValidationException(detail="Stored procedure params must be a list or tuple.")

                cursor.callproc(procedure_name, list(params))
                rows = self._fetch_cursor_rows(cursor)
                self._log(
                    execution_log,
                    stage="CONNECTOR_DATABASE_SP",
                    message="Stored procedure executed.",
                    metadata={
                        "procedure": procedure_name,
                        "row_count": len(rows),
                    },
                )
                return {
                    "mode": "stored_procedure",
                    "database_alias": db_alias,
                    "procedure": procedure_name,
                    "params": list(params),
                    "rows": rows,
                    "row_count": len(rows),
                    "duration_ms": round((perf_counter() - started_at) * 1000, 3),
                }

            query = str(payload.get("query") or config_json.get("query") or "").strip()
            if not query:
                raise ValidationException(detail="Database query is required.")

            normalized_query = query.lower().lstrip()
            if not normalized_query.startswith(("select", "with", "insert", "update", "delete")):
                raise ValidationException(
                    detail="Only SELECT/WITH/INSERT/UPDATE/DELETE queries are supported."
                )

            params = payload.get("params") or config_json.get("params") or []
            if params is None:
                params = []

            cursor.execute(query, params)
            rows = self._fetch_cursor_rows(cursor)
            affected_rows = cursor.rowcount

        self._log(
            execution_log,
            stage="CONNECTOR_DATABASE_QUERY",
            message="Database query executed.",
            metadata={
                "database_alias": db_alias,
                "affected_rows": affected_rows,
                "result_rows": len(rows),
            },
        )
        return {
            "mode": "database",
            "database_alias": db_alias,
            "query": query,
            "params": params,
            "rows": rows,
            "row_count": len(rows),
            "affected_rows": affected_rows,
            "duration_ms": round((perf_counter() - started_at) * 1000, 3),
        }

    def execute_rest(
        self,
        *,
        connector: Connector,
        configuration: ConnectorConfiguration | None,
        payload: dict[str, Any],
        context: dict[str, Any],
        execution_log: list[dict[str, Any]],
    ) -> dict[str, Any]:
        config_json = self._configuration_json(configuration)
        endpoint = str(payload.get("endpoint") or config_json.get("endpoint") or connector.api_base_url or "")
        url = self._resolve_endpoint(connector.api_base_url, endpoint)
        if not url:
            raise ValidationException(detail="REST endpoint is required.")

        method = str(payload.get("method") or config_json.get("method") or "GET").upper()
        timeout = int(payload.get("timeout") or connector.timeout)
        retries = int(payload.get("retries") or connector.retry_count)

        headers = self._headers_json(configuration)
        headers.update(self._build_auth_headers(connector, configuration))

        payload_headers = payload.get("headers")
        if isinstance(payload_headers, dict):
            headers.update({str(key): str(value) for key, value in payload_headers.items()})

        params = payload.get("query_params") or payload.get("params") or {}
        if not isinstance(params, dict):
            raise ValidationException(detail="REST query params must be a JSON object.")

        request_json = payload.get("json")
        request_data = payload.get("data")
        if request_json is None and isinstance(payload.get("body"), dict):
            request_json = payload.get("body")
        elif request_data is None and payload.get("body") is not None:
            request_data = payload.get("body")

        if isinstance(request_data, str):
            request_data = self._resolve_placeholders(
                request_data,
                {"payload": payload, "context": context, **context},
            )

        attempts = max(1, retries + 1)
        started_at = perf_counter()
        last_exception: Exception | None = None

        for attempt in range(1, attempts + 1):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=request_json,
                    data=request_data,
                    timeout=timeout,
                )

                if response.status_code >= 500 and attempt < attempts:
                    continue

                content_type = response.headers.get("Content-Type", "")
                response_body: Any
                if "application/json" in content_type:
                    try:
                        response_body = response.json()
                    except ValueError:
                        response_body = response.text
                else:
                    response_body = response.text

                self._log(
                    execution_log,
                    stage="CONNECTOR_REST_EXECUTED",
                    message="REST connector executed.",
                    metadata={
                        "url": url,
                        "method": method,
                        "status_code": response.status_code,
                        "attempt": attempt,
                    },
                )

                return {
                    "mode": "rest",
                    "url": url,
                    "method": method,
                    "status_code": response.status_code,
                    "ok": response.ok,
                    "headers": dict(response.headers),
                    "response": response_body,
                    "duration_ms": round((perf_counter() - started_at) * 1000, 3),
                }
            except requests.RequestException as exc:
                last_exception = exc
                if attempt >= attempts:
                    break

        raise ExternalServiceException(detail=f"REST connector execution failed: {last_exception}")

    def execute_soap(
        self,
        *,
        connector: Connector,
        configuration: ConnectorConfiguration | None,
        payload: dict[str, Any],
        context: dict[str, Any],
        execution_log: list[dict[str, Any]],
    ) -> dict[str, Any]:
        config_json = self._configuration_json(configuration)
        endpoint = str(
            payload.get("soap_endpoint")
            or payload.get("endpoint")
            or config_json.get("soap_endpoint")
            or config_json.get("endpoint")
            or connector.api_base_url
            or ""
        )
        url = self._resolve_endpoint(connector.api_base_url, endpoint)
        if not url:
            raise ValidationException(detail="SOAP endpoint is required.")

        action = str(
            payload.get("soap_action")
            or payload.get("action")
            or config_json.get("soap_action")
            or ""
        ).strip()

        envelope = str(
            payload.get("envelope")
            or payload.get("xml")
            or config_json.get("soap_envelope")
            or ""
        ).strip()

        if not envelope:
            action_element = action or "Execute"
            envelope = (
                "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\">"
                f"<soapenv:Body><{action_element}/></soapenv:Body>"
                "</soapenv:Envelope>"
            )

        envelope = self._resolve_placeholders(
            envelope,
            {
                "payload": payload,
                "context": context,
                **context,
            },
        )

        timeout = int(payload.get("timeout") or connector.timeout)
        headers = {
            "Content-Type": "text/xml; charset=utf-8",
            **self._headers_json(configuration),
            **self._build_auth_headers(connector, configuration),
        }
        if action:
            headers["SOAPAction"] = action

        started_at = perf_counter()
        try:
            response = self.session.post(
                url,
                data=envelope.encode("utf-8"),
                headers=headers,
                timeout=timeout,
            )
        except requests.RequestException as exc:
            raise ExternalServiceException(detail=f"SOAP connector execution failed: {exc}") from exc

        response_xml = response.text
        parsed_xml: dict[str, Any] | list[Any] | str
        try:
            xml_root = ET.fromstring(response_xml)
            parsed_xml = {xml_root.tag: self._xml_to_dict(xml_root)}
        except ET.ParseError:
            parsed_xml = response_xml

        self._log(
            execution_log,
            stage="CONNECTOR_SOAP_EXECUTED",
            message="SOAP connector executed.",
            metadata={
                "url": url,
                "status_code": response.status_code,
                "soap_action": action,
            },
        )

        return {
            "mode": "soap",
            "url": url,
            "soap_action": action,
            "status_code": response.status_code,
            "ok": response.ok,
            "response_xml": response_xml,
            "parsed_response": parsed_xml,
            "duration_ms": round((perf_counter() - started_at) * 1000, 3),
        }

    def _execute_queue_future(
        self,
        *,
        connector: Connector,
        configuration: ConnectorConfiguration | None,
        payload: dict[str, Any],
        context: dict[str, Any],
        execution_log: list[dict[str, Any]],
    ) -> dict[str, Any]:
        config_json = self._configuration_json(configuration)
        queue_name = str(payload.get("queue_name") or config_json.get("queue_name") or connector.code).strip()
        if not queue_name:
            raise ValidationException(detail="queue_name is required for queue execution.")

        message_id = str(uuid.uuid4())
        queued_payload = {
            "message_id": message_id,
            "queue_name": queue_name,
            "payload": payload.get("message") or payload.get("body") or payload,
            "context": context,
            "queued_at": timezone.now().isoformat(),
        }

        self._log(
            execution_log,
            stage="CONNECTOR_QUEUE_ENQUEUED",
            message="Queue payload prepared for asynchronous delivery.",
            metadata={"queue_name": queue_name, "message_id": message_id},
        )

        return {
            "mode": "queue",
            "queued": True,
            "queue_name": queue_name,
            "message": queued_payload,
        }

    def execute_connector(
        self,
        *,
        connector_code: str,
        payload: Any = None,
        operation: str = "",
        context: Any = None,
        perform_validation: bool = True,
    ) -> dict[str, Any]:
        connector, configuration = self._load_connector(connector_code)
        payload_dict = self._ensure_dict(payload, "payload")
        context_dict = self._ensure_dict(context, "context")

        execution_mode = self._resolve_execution_mode(
            connector=connector,
            configuration=configuration,
            operation=operation,
            payload=payload_dict,
        )

        execution_log: list[dict[str, Any]] = []
        started_at = perf_counter()
        self._log(
            execution_log,
            stage="CONNECTOR_EXECUTION_START",
            message="Connector execution started.",
            metadata={
                "connector_code": connector.code,
                "connector_type": connector.connector_type,
                "execution_mode": execution_mode,
            },
        )

        connection_validation: dict[str, Any] | None = None
        if perform_validation:
            connection_validation = self._validate_connection_internal(
                connector=connector,
                configuration=configuration,
                execution_mode=execution_mode,
                payload=payload_dict,
            )
            self._log(
                execution_log,
                stage="CONNECTOR_VALIDATED",
                message="Connector validation completed.",
                metadata=connection_validation,
            )

        try:
            if execution_mode in {"database", "stored_procedure"}:
                response = self.execute_database(
                    connector=connector,
                    configuration=configuration,
                    payload=payload_dict,
                    operation=operation,
                    execution_log=execution_log,
                )
            elif execution_mode == "rest":
                response = self.execute_rest(
                    connector=connector,
                    configuration=configuration,
                    payload=payload_dict,
                    context=context_dict,
                    execution_log=execution_log,
                )
            elif execution_mode == "soap":
                response = self.execute_soap(
                    connector=connector,
                    configuration=configuration,
                    payload=payload_dict,
                    context=context_dict,
                    execution_log=execution_log,
                )
            elif execution_mode == "queue":
                response = self._execute_queue_future(
                    connector=connector,
                    configuration=configuration,
                    payload=payload_dict,
                    context=context_dict,
                    execution_log=execution_log,
                )
            else:
                raise ValidationException(detail=f"Unsupported connector execution mode '{execution_mode}'.")
        except requests.RequestException as exc:
            raise ExternalServiceException(detail=f"Connector request failed: {exc}") from exc

        duration_ms = round((perf_counter() - started_at) * 1000, 3)
        self._log(
            execution_log,
            stage="CONNECTOR_EXECUTION_COMPLETE",
            message="Connector execution completed.",
            metadata={"duration_ms": duration_ms, "execution_mode": execution_mode},
        )

        return {
            "connector_code": connector.code,
            "connector_name": connector.name,
            "connector_type": connector.connector_type,
            "execution_mode": execution_mode,
            "connection_validation": connection_validation,
            "response": response,
            "duration_ms": duration_ms,
            "execution_log": execution_log,
        }
