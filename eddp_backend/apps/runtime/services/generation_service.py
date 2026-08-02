from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from apps.common.choices import OutputFormatChoices, StatusChoices
from apps.common.exceptions import (
    BaseApplicationException,
    ResourceNotFoundException,
    ValidationException,
)
from apps.common.responses import error_response, success_response
from apps.governance.services import GovernanceIntegrationService

from ..repositories import RuntimeEngineRepository
from .authorization import RuntimeAuthorizationService
from .connector_engine import ConnectorExecutionService
from .docx_generator import DOCXGeneratorService
from .html_builder import HTMLBuilderService
from .pdf_generator import PDFGeneratorService
from .rule_engine import RuleExecutionService
from .template_renderer import TemplateRenderingService
from .variable_resolver import VariableResolverService


class GenerationService:
    """End-to-end runtime generation orchestration for preview and generation APIs."""

    def __init__(
        self,
        engine_repository: RuntimeEngineRepository | None = None,
        variable_resolver_service: VariableResolverService | None = None,
        rule_execution_service: RuleExecutionService | None = None,
        connector_execution_service: ConnectorExecutionService | None = None,
        template_rendering_service: TemplateRenderingService | None = None,
        html_builder_service: HTMLBuilderService | None = None,
        pdf_generator_service: PDFGeneratorService | None = None,
        docx_generator_service: DOCXGeneratorService | None = None,
        governance_integration_service: GovernanceIntegrationService | None = None,
        authorization_service: RuntimeAuthorizationService | None = None,
    ) -> None:
        self.engine_repository = engine_repository or RuntimeEngineRepository()
        self.variable_resolver_service = variable_resolver_service or VariableResolverService(
            repository=self.engine_repository
        )
        self.rule_execution_service = rule_execution_service or RuleExecutionService(
            repository=self.engine_repository
        )
        self.connector_execution_service = connector_execution_service or ConnectorExecutionService(
            repository=self.engine_repository
        )
        self.template_rendering_service = template_rendering_service or TemplateRenderingService(
            repository=self.engine_repository
        )
        self.html_builder_service = html_builder_service or HTMLBuilderService()
        self.pdf_generator_service = pdf_generator_service or PDFGeneratorService(
            repository=self.engine_repository
        )
        self.docx_generator_service = docx_generator_service or DOCXGeneratorService(
            repository=self.engine_repository
        )
        self.governance_integration_service = governance_integration_service or GovernanceIntegrationService()
        self.authorization_service = authorization_service or RuntimeAuthorizationService()

    @staticmethod
    def _error(exc: BaseApplicationException) -> Response:
        detail = exc.detail
        message = detail if isinstance(detail, str) else "Request failed."
        errors = exc.errors if getattr(exc, "errors", None) else detail
        return error_response(
            message=message,
            errors=errors,
            status_code=exc.status_code,
            error_code=getattr(exc, "default_code", "application_error"),
        )

    @staticmethod
    def _validate_payload(data: dict[str, Any]) -> None:
        if not isinstance(data, dict):
            raise ValidationException(detail="Payload must be a JSON object.")

    @staticmethod
    def _stage_record(
        *,
        stage: str,
        status_value: str,
        started_at,
        completed_at,
        details: dict[str, Any] | None,
    ) -> dict[str, Any]:
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        return {
            "stage": stage,
            "status": status_value,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_ms": max(0, duration_ms),
            "details": details or {},
        }

    @staticmethod
    def _serialize_stage_records(stage_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        serialized: list[dict[str, Any]] = []
        for item in stage_records:
            started_at = item.get("started_at")
            completed_at = item.get("completed_at")
            serialized.append(
                {
                    "stage": item.get("stage"),
                    "status": item.get("status"),
                    "started_at": started_at.isoformat() if started_at else None,
                    "completed_at": completed_at.isoformat() if completed_at else None,
                    "duration_ms": int(item.get("duration_ms") or 0),
                    "details": item.get("details") or {},
                }
            )
        return serialized

    @staticmethod
    def _serialize_generated_document(generated_document) -> dict[str, Any]:
        if generated_document is None:
            return {}
        return {
            "id": str(generated_document.id),
            "code": generated_document.code,
            "file_name": generated_document.file_name,
            "file_path": generated_document.file_path,
            "file_type": generated_document.file_type,
            "file_size": generated_document.file_size,
            "checksum": generated_document.checksum,
            "generated_at": generated_document.generated_at.isoformat()
            if generated_document.generated_at
            else None,
        }

    @staticmethod
    def _build_urls(request, generation_request, generated_document) -> dict[str, str]:
        if generated_document is None:
            return {}

        download_path = f"/api/runtime/download/{generation_request.request_id}"
        media_path = (
            f"{str(settings.MEDIA_URL).rstrip('/')}/{str(generated_document.file_path).lstrip('/')}"
        )

        if request is None:
            return {
                "download_url": download_path,
                "file_url": media_path,
            }

        return {
            "download_url": request.build_absolute_uri(download_path),
            "file_url": request.build_absolute_uri(media_path),
        }

    def _get_generation_request_or_raise(self, generation_request_id: Any):
        if not generation_request_id:
            raise ValidationException(detail="generation_request_id is required.")
        generation_request = self.engine_repository.get_generation_request_by_id(generation_request_id)
        if generation_request is None:
            raise ResourceNotFoundException(detail="Generation request not found.")
        return generation_request

    @staticmethod
    def _build_generation_request_code() -> str:
        return f"GRQ-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def _build_business_reference() -> str:
        return f"BR-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def _resolve_reference_value(data: dict[str, Any]) -> str:
        business_reference = str(data.get("business_reference") or "").strip()
        correlation_id = str(data.get("correlation_id") or "").strip()
        return business_reference or correlation_id

    def _resolve_template_version_for_preview(self, data: dict[str, Any]):
        template_version_id = data.get("template_version_id")
        if template_version_id:
            template_version = self.engine_repository.get_template_version_by_id(template_version_id)
            if template_version is None:
                raise ResourceNotFoundException(detail="Template version not found.")
            return template_version

        template_version_code = str(data.get("template_version_code") or "").strip()
        if template_version_code:
            template_version = self.engine_repository.get_template_version_by_code(template_version_code)
            if template_version is None:
                raise ResourceNotFoundException(detail="Template version not found.")
            return template_version

        template_code = str(data.get("template_code") or "").strip()
        if template_code:
            template = self.engine_repository.get_template_by_code(template_code)
            if template is None:
                raise ResourceNotFoundException(detail="Template not found.")

            template_version = self.engine_repository.get_active_template_version(template)
            if template_version is None:
                raise ValidationException(detail="No active template version found for selected template.")
            return template_version

        return None

    def _resolve_document_for_preview(self, data: dict[str, Any]):
        document_id = data.get("document_id")
        if not document_id:
            return None

        document = self.engine_repository.get_document_by_id(document_id)
        if document is None:
            raise ResourceNotFoundException(detail="Document not found.")
        return document

    def _ensure_generation_request_for_preview(self, *, request, data: dict[str, Any]):
        generation_request_id = data.get("generation_request_id")
        if generation_request_id:
            return self._get_generation_request_or_raise(generation_request_id)

        runtime_payload = self._normalize_dict(data.get("runtime_payload") or {}, "runtime_payload")
        template_version = self._resolve_template_version_for_preview(data)
        document = self._resolve_document_for_preview(data)

        if template_version is None and document is not None:
            default_template = self.engine_repository.get_default_template_for_document(document)
            if default_template is None:
                raise ValidationException(detail="No template configured for selected document.")

            template_version = self.engine_repository.get_active_template_version(default_template)
            if template_version is None:
                raise ValidationException(detail="No active template version found for selected document.")

        if template_version is None:
            raise ValidationException(detail="Template details are required to create runtime request.")

        if document is None:
            document = template_version.template.document

        if template_version.template.document_id != document.id:
            raise ValidationException(detail="Selected template does not belong to selected document.")

        request_source = str(data.get("request_source") or "PREVIEW").strip() or "PREVIEW"
        business_reference = self._resolve_reference_value(data) or self._build_business_reference()

        request_user = getattr(request, "user", None)
        if request_user is not None and not getattr(request_user, "is_authenticated", False):
            request_user = None

        return self.engine_repository.create_generation_request(
            {
                "code": self._build_generation_request_code(),
                "document": document,
                "template_version": template_version,
                "request_source": request_source,
                "business_reference": business_reference,
                "input_payload": runtime_payload,
                "requested_by": request_user,
                "created_by": request_user,
                "updated_by": request_user,
                "status": StatusChoices.DRAFT,
            }
        )

    def _get_generation_request_by_request_id_or_raise(self, request_id: Any):
        if not request_id:
            raise ValidationException(detail="request_id is required.")
        generation_request = self.engine_repository.get_generation_request_by_request_id(request_id)
        if generation_request is None:
            raise ResourceNotFoundException(detail="Generation request not found.")
        return generation_request

    def _resolve_document_definition(self, generation_request):
        return self.engine_repository.get_document_definition_by_document_code(
            generation_request.document.code
        )

    @staticmethod
    def _normalize_dict(value: Any, field_name: str) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValidationException(detail=f"{field_name} must be a JSON object.")
        return value

    @staticmethod
    def _normalize_connector_steps(raw_steps: Any) -> list[dict[str, Any]]:
        if raw_steps is None:
            return []
        if not isinstance(raw_steps, list):
            raise ValidationException(detail="connectors must be an array.")

        normalized: list[dict[str, Any]] = []
        for item in raw_steps:
            if not isinstance(item, dict):
                raise ValidationException(detail="Each connector step must be a JSON object.")

            connector_code = str(item.get("connector_code") or "").strip()
            if not connector_code:
                raise ValidationException(detail="connector_code is required in each connector step.")

            payload = item.get("payload") or {}
            if not isinstance(payload, dict):
                raise ValidationException(detail="connector payload must be a JSON object.")

            normalized.append(
                {
                    "connector_code": connector_code,
                    "operation": str(item.get("operation") or "").strip(),
                    "payload": payload,
                    "perform_validation": bool(item.get("perform_validation", True)),
                }
            )
        return normalized

    def _execute_runtime_flow(
        self,
        *,
        generation_request,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        definition = self._resolve_document_definition(generation_request)

        variable_group_code = str(
            data.get("variable_group_code")
            or (definition.variable_group_code if definition else "")
            or ""
        ).strip()
        rule_group_code = str(
            data.get("rule_group_code")
            or (definition.rule_group_code if definition else "")
            or ""
        ).strip()
        default_connector_code = str(
            data.get("connector_code")
            or (definition.connector_code if definition else "")
            or ""
        ).strip()

        template_code = str(
            data.get("template_code")
            or (definition.active_template_code if definition else "")
            or ""
        ).strip()
        template_version_code = str(data.get("template_version_code") or "").strip()
        template_version_id = data.get("template_version_id") or generation_request.template_version_id

        runtime_payload = self._normalize_dict(
            data.get("runtime_payload") or generation_request.input_payload or {},
            "runtime_payload",
        )
        database_values = self._normalize_dict(data.get("database_values") or {}, "database_values")
        connector_values_seed = self._normalize_dict(data.get("connector_values") or {}, "connector_values")
        computed_values = self._normalize_dict(data.get("computed_values") or {}, "computed_values")
        render_options = self._normalize_dict(data.get("render_options") or {}, "render_options")
        layout_options = self._normalize_dict(data.get("layout_options") or {}, "layout_options")

        style_overrides = data.get("style_overrides") or ""
        if style_overrides and not isinstance(style_overrides, str):
            raise ValidationException(detail="style_overrides must be a string.")

        connector_steps = self._normalize_connector_steps(data.get("connectors") or [])
        if not connector_steps and default_connector_code:
            connector_payload = self._normalize_dict(data.get("connector_payload") or {}, "connector_payload")
            connector_steps = [
                {
                    "connector_code": default_connector_code,
                    "operation": "",
                    "payload": connector_payload,
                    "perform_validation": True,
                }
            ]

        if not template_code and not template_version_code and not template_version_id:
            raise ValidationException(detail="Template details are required to render document.")

        execution_log: list[dict[str, Any]] = []
        stage_records: list[dict[str, Any]] = []

        resolved_variables: dict[str, Any] = {}
        executed_rules: list[dict[str, Any]] = []
        connector_response: dict[str, Any] = dict(connector_values_seed)
        validation_results: dict[str, Any] = {}

        if variable_group_code:
            variable_stage_start = timezone.now()
            try:
                variable_result = self.variable_resolver_service.resolve_variables(
                    variable_group_code=variable_group_code,
                    runtime_payload=runtime_payload,
                    database_values=database_values,
                    connector_values=connector_values_seed,
                    computed_values=computed_values,
                )
                resolved_variables = variable_result.get("resolved_variables") or {}
                validation_results["variable_resolution"] = (
                    variable_result.get("validation_results") or {}
                )
                execution_log.extend(variable_result.get("execution_log") or [])

                variable_stage_end = timezone.now()
                stage_records.append(
                    self._stage_record(
                        stage="RESOLVE_VARIABLES",
                        status_value="SUCCESS",
                        started_at=variable_stage_start,
                        completed_at=variable_stage_end,
                        details={
                            "variable_group_code": variable_group_code,
                            "resolved_count": len(resolved_variables),
                        },
                    )
                )
            except BaseApplicationException as exc:
                variable_stage_end = timezone.now()
                stage_records.append(
                    self._stage_record(
                        stage="RESOLVE_VARIABLES",
                        status_value="FAILED",
                        started_at=variable_stage_start,
                        completed_at=variable_stage_end,
                        details={"error": str(exc.detail)},
                    )
                )
                raise

        if rule_group_code:
            rules_stage_start = timezone.now()
            try:
                rules_runtime_context = {
                    "resolved_variables": resolved_variables,
                    "variables": resolved_variables,
                    "connector_response": connector_response,
                }
                rule_result = self.rule_execution_service.execute_rules(
                    rule_group_code=rule_group_code,
                    runtime_context=rules_runtime_context,
                    stop_on_critical_failure=bool(data.get("stop_on_critical_failure", True)),
                )
                executed_rules = rule_result.get("executed_rules") or []
                validation_results["rule_execution"] = rule_result.get("validation_results") or {}
                execution_log.extend(rule_result.get("execution_log") or [])

                runtime_context_after_rules = rule_result.get("runtime_context") or {}
                if isinstance(runtime_context_after_rules, dict):
                    rule_variables = runtime_context_after_rules.get("variables")
                    if isinstance(rule_variables, dict):
                        resolved_variables.update(rule_variables)

                rules_stage_end = timezone.now()
                stage_records.append(
                    self._stage_record(
                        stage="EXECUTE_RULES",
                        status_value="SUCCESS",
                        started_at=rules_stage_start,
                        completed_at=rules_stage_end,
                        details={
                            "rule_group_code": rule_group_code,
                            "executed_count": len(executed_rules),
                            "summary": rule_result.get("summary") or {},
                        },
                    )
                )
            except BaseApplicationException as exc:
                rules_stage_end = timezone.now()
                stage_records.append(
                    self._stage_record(
                        stage="EXECUTE_RULES",
                        status_value="FAILED",
                        started_at=rules_stage_start,
                        completed_at=rules_stage_end,
                        details={"error": str(exc.detail)},
                    )
                )
                raise

        if connector_steps:
            connectors_stage_start = timezone.now()
            connector_results: list[dict[str, Any]] = []
            try:
                for step in connector_steps:
                    step_result = self.connector_execution_service.execute_connector(
                        connector_code=step["connector_code"],
                        payload=step["payload"],
                        operation=step["operation"],
                        context={
                            "variables": resolved_variables,
                            "resolved_variables": resolved_variables,
                            "connector_response": connector_response,
                            "runtime_payload": runtime_payload,
                        },
                        perform_validation=bool(step["perform_validation"]),
                    )
                    connector_response[step["connector_code"]] = step_result.get("response")
                    connector_results.append(step_result)
                    execution_log.extend(step_result.get("execution_log") or [])

                connectors_stage_end = timezone.now()
                stage_records.append(
                    self._stage_record(
                        stage="EXECUTE_CONNECTORS",
                        status_value="SUCCESS",
                        started_at=connectors_stage_start,
                        completed_at=connectors_stage_end,
                        details={
                            "connector_count": len(connector_results),
                            "connectors": [item.get("connector_code") for item in connector_results],
                        },
                    )
                )
            except BaseApplicationException as exc:
                connectors_stage_end = timezone.now()
                stage_records.append(
                    self._stage_record(
                        stage="EXECUTE_CONNECTORS",
                        status_value="FAILED",
                        started_at=connectors_stage_start,
                        completed_at=connectors_stage_end,
                        details={"error": str(exc.detail)},
                    )
                )
                raise

        render_variables = dict(resolved_variables)
        render_variables.setdefault("connector_response", connector_response)
        render_variables.setdefault("executed_rules", executed_rules)

        render_stage_start = timezone.now()
        try:
            render_result = self.template_rendering_service.render_template(
                template_code=template_code,
                template_version_code=template_version_code,
                template_version_id=template_version_id,
                variables=render_variables,
                options=render_options,
            )
            execution_log.extend(render_result.get("execution_log") or [])
            render_stage_end = timezone.now()
            stage_records.append(
                self._stage_record(
                    stage="RENDER_TEMPLATE",
                    status_value="SUCCESS",
                    started_at=render_stage_start,
                    completed_at=render_stage_end,
                    details={
                        "template_code": render_result.get("template_code"),
                        "template_version_code": render_result.get("template_version_code"),
                    },
                )
            )
        except BaseApplicationException as exc:
            render_stage_end = timezone.now()
            stage_records.append(
                self._stage_record(
                    stage="RENDER_TEMPLATE",
                    status_value="FAILED",
                    started_at=render_stage_start,
                    completed_at=render_stage_end,
                    details={"error": str(exc.detail)},
                )
            )
            raise

        html_stage_start = timezone.now()
        try:
            html_result = self.html_builder_service.build_html(
                template_name=render_result.get("template_name") or "Document",
                body_html=render_result.get("body_html") or "",
                header_html=render_result.get("header_html") or "",
                footer_html=render_result.get("footer_html") or "",
                variables=render_variables,
                options=layout_options,
                style_overrides=style_overrides,
            )
            execution_log.extend(html_result.get("execution_log") or [])
            html_stage_end = timezone.now()
            stage_records.append(
                self._stage_record(
                    stage="BUILD_HTML",
                    status_value="SUCCESS",
                    started_at=html_stage_start,
                    completed_at=html_stage_end,
                    details={
                        "page_size": html_result.get("page_size"),
                        "orientation": html_result.get("orientation"),
                    },
                )
            )
        except BaseApplicationException as exc:
            html_stage_end = timezone.now()
            stage_records.append(
                self._stage_record(
                    stage="BUILD_HTML",
                    status_value="FAILED",
                    started_at=html_stage_start,
                    completed_at=html_stage_end,
                    details={"error": str(exc.detail)},
                )
            )
            raise

        self.engine_repository.upsert_runtime_context(
            generation_request=generation_request,
            resolved_variables=resolved_variables,
            executed_rules=executed_rules,
            validation_results=validation_results,
            connector_response=connector_response,
            execution_log_entries=execution_log,
        )

        return {
            "resolved_variables": resolved_variables,
            "executed_rules": executed_rules,
            "connector_response": connector_response,
            "validation_results": validation_results,
            "render_result": render_result,
            "html_result": html_result,
            "execution_log": execution_log,
            "stage_records": stage_records,
        }

    def preview_document(self, *, request, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            security_context = self.authorization_service.authorize(
                request=request,
                action="preview",
                data=data,
            )

            generation_request = self._ensure_generation_request_for_preview(request=request, data=data)
            flow_result = self._execute_runtime_flow(generation_request=generation_request, data=data)

            governance_result = self.governance_integration_service.record_preview(
                generation_request=generation_request,
                execution_history=flow_result["stage_records"],
                request=request,
                performed_by=getattr(request, "user", None),
            )

            return success_response(
                data={
                    "generation_request_id": str(generation_request.id),
                    "request_id": str(generation_request.request_id),
                    "business_reference": generation_request.business_reference,
                    "correlation_id": generation_request.business_reference,
                    "template_code": flow_result["render_result"].get("template_code"),
                    "template_version_code": flow_result["render_result"].get("template_version_code"),
                    "html": flow_result["html_result"].get("html"),
                    "page_size": flow_result["html_result"].get("page_size"),
                    "orientation": flow_result["html_result"].get("orientation"),
                    "security": security_context,
                    "governance": governance_result,
                    "execution_history": self._serialize_stage_records(flow_result["stage_records"]),
                },
                message="Preview generated successfully.",
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def generate_document(self, *, request, data: dict[str, Any]) -> Response:
        generation_request = None
        try:
            self._validate_payload(data)
            security_context = self.authorization_service.authorize(
                request=request,
                action="generate",
                data=data,
            )

            generation_request = self._get_generation_request_or_raise(data.get("generation_request_id"))
            self.engine_repository.update_generation_request_status(
                generation_request=generation_request,
                status_value=StatusChoices.ACTIVE,
                completed=False,
            )

            flow_result = self._execute_runtime_flow(generation_request=generation_request, data=data)

            output_format = str(data.get("output_format") or OutputFormatChoices.PDF).strip().upper()
            if output_format not in {OutputFormatChoices.PDF, OutputFormatChoices.DOCX}:
                raise ValidationException(detail="output_format must be PDF or DOCX.")

            generation_stage_start = timezone.now()
            if output_format == OutputFormatChoices.DOCX:
                generation_result = self.docx_generator_service.generate_docx(
                    generation_request=generation_request,
                    html_content=flow_result["html_result"].get("body_html") or "",
                    header_html=flow_result["html_result"].get("header_html") or "",
                    footer_html=flow_result["html_result"].get("footer_html") or "",
                    file_name=str(data.get("file_name") or ""),
                    document_title=flow_result["render_result"].get("template_name") or "Document",
                )
            else:
                generation_result = self.pdf_generator_service.generate_pdf(
                    generation_request=generation_request,
                    html_content=flow_result["html_result"].get("html") or "",
                    file_name=str(data.get("file_name") or ""),
                )

            generation_stage_end = timezone.now()
            flow_result["stage_records"].append(
                self._stage_record(
                    stage="GENERATE_FILE",
                    status_value="SUCCESS",
                    started_at=generation_stage_start,
                    completed_at=generation_stage_end,
                    details={
                        "output_format": output_format,
                        "file_name": generation_result.get("file_name"),
                        "file_size": generation_result.get("file_size"),
                    },
                )
            )

            self.engine_repository.upsert_runtime_context(
                generation_request=generation_request,
                execution_log_entries=generation_result.get("execution_log") or [],
            )

            generated_document = self.engine_repository.get_generated_document_by_generation_request(
                generation_request
            )
            if generated_document is None:
                raise ResourceNotFoundException(detail="Generated document could not be persisted.")

            self.engine_repository.update_generation_request_status(
                generation_request=generation_request,
                status_value=StatusChoices.PUBLISHED,
                completed=True,
            )

            governance_result = self.governance_integration_service.record_generation(
                generation_request=generation_request,
                generated_document=generated_document,
                output_format=output_format,
                variable_count=len(flow_result.get("resolved_variables") or {}),
                rule_count=len(flow_result.get("executed_rules") or []),
                connector_count=len(flow_result.get("connector_response") or {}),
                execution_history=flow_result["stage_records"],
                request=request,
                performed_by=getattr(request, "user", None),
            )

            urls = self._build_urls(request, generation_request, generated_document)
            return success_response(
                data={
                    "generation_request_id": str(generation_request.id),
                    "request_id": str(generation_request.request_id),
                    "business_reference": generation_request.business_reference,
                    "correlation_id": generation_request.business_reference,
                    "status": StatusChoices.PUBLISHED,
                    "security": security_context,
                    "generated_document": self._serialize_generated_document(generated_document),
                    "download_url": urls.get("download_url"),
                    "file_url": urls.get("file_url"),
                    "governance": governance_result,
                    "execution_history": self._serialize_stage_records(flow_result["stage_records"]),
                },
                message="Document generated successfully.",
                status_code=status.HTTP_201_CREATED,
            )
        except BaseApplicationException as exc:
            if generation_request is not None:
                self.engine_repository.update_generation_request_status(
                    generation_request=generation_request,
                    status_value=StatusChoices.INACTIVE,
                    completed=False,
                )
            return self._error(exc)

    def download_document(self, *, request, request_id: Any) -> Response:
        try:
            security_context = self.authorization_service.authorize(
                request=request,
                action="download",
                data={},
            )

            generation_request = self._get_generation_request_by_request_id_or_raise(request_id)
            generated_document = self.engine_repository.get_generated_document_by_generation_request(
                generation_request
            )
            if generated_document is None:
                raise ResourceNotFoundException(detail="Generated document not found for this request.")

            governance_result = self.governance_integration_service.record_download(
                generation_request=generation_request,
                generated_document=generated_document,
                request=request,
                performed_by=getattr(request, "user", None),
            )

            urls = self._build_urls(request, generation_request, generated_document)
            return success_response(
                data={
                    "request_id": str(generation_request.request_id),
                    "business_reference": generation_request.business_reference,
                    "correlation_id": generation_request.business_reference,
                    "status": generation_request.status,
                    "security": security_context,
                    "generated_document": self._serialize_generated_document(generated_document),
                    "download_url": urls.get("download_url"),
                    "file_url": urls.get("file_url"),
                    "governance": governance_result,
                },
                message="Download URL generated successfully.",
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def generation_status(self, *, request, request_id: Any) -> Response:
        try:
            security_context = self.authorization_service.authorize(
                request=request,
                action="status",
                data={},
            )

            generation_request = self._get_generation_request_by_request_id_or_raise(request_id)
            generated_document = self.engine_repository.get_generated_document_by_generation_request(
                generation_request
            )

            metric = self.governance_integration_service.repository.get_generation_metric(generation_request)
            execution_history = list(
                self.governance_integration_service.repository.get_execution_history(generation_request)
            )

            urls = self._build_urls(request, generation_request, generated_document)

            return success_response(
                data={
                    "request_id": str(generation_request.request_id),
                    "generation_request_id": str(generation_request.id),
                    "business_reference": generation_request.business_reference,
                    "correlation_id": generation_request.business_reference,
                    "status": generation_request.status,
                    "requested_at": generation_request.requested_at.isoformat()
                    if generation_request.requested_at
                    else None,
                    "completed_at": generation_request.completed_at.isoformat()
                    if generation_request.completed_at
                    else None,
                    "processing_time_ms": generation_request.processing_time_ms,
                    "security": security_context,
                    "generated_document": self._serialize_generated_document(generated_document),
                    "download_url": urls.get("download_url"),
                    "file_url": urls.get("file_url"),
                    "generation_metric": {
                        "id": str(metric.id),
                        "code": metric.code,
                        "output_format": metric.output_format,
                        "processing_time_ms": metric.processing_time_ms,
                        "variable_count": metric.variable_count,
                        "rule_count": metric.rule_count,
                        "connector_count": metric.connector_count,
                        "recorded_on": metric.recorded_on.isoformat() if metric.recorded_on else None,
                        "metric_json": metric.metric_json,
                    }
                    if metric
                    else {},
                    "execution_history": [
                        {
                            "stage_name": item.stage_name,
                            "stage_status": item.stage_status,
                            "sequence_no": item.sequence_no,
                            "started_at": item.started_at.isoformat() if item.started_at else None,
                            "completed_at": item.completed_at.isoformat() if item.completed_at else None,
                            "duration_ms": item.duration_ms,
                            "details_json": item.details_json,
                        }
                        for item in execution_history
                    ],
                },
                message="Generation status fetched successfully.",
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def generation_history(self, *, request, business_reference: str) -> Response:
        try:
            security_context = self.authorization_service.authorize(
                request=request,
                action="history",
                data={},
            )

            reference = (business_reference or "").strip()
            if not reference:
                raise ValidationException(detail="business_reference is required.")

            generation_requests = list(
                self.engine_repository.get_generation_requests_by_business_reference(reference)
            )

            history_items: list[dict[str, Any]] = []
            for generation_request in generation_requests:
                generated_document = self.engine_repository.get_generated_document_by_generation_request(
                    generation_request
                )
                urls = self._build_urls(request, generation_request, generated_document)
                history_items.append(
                    {
                        "request_id": str(generation_request.request_id),
                        "generation_request_id": str(generation_request.id),
                        "business_reference": generation_request.business_reference,
                        "correlation_id": generation_request.business_reference,
                        "status": generation_request.status,
                        "request_source": generation_request.request_source,
                        "requested_at": generation_request.requested_at.isoformat()
                        if generation_request.requested_at
                        else None,
                        "completed_at": generation_request.completed_at.isoformat()
                        if generation_request.completed_at
                        else None,
                        "processing_time_ms": generation_request.processing_time_ms,
                        "generated_document": self._serialize_generated_document(generated_document),
                        "download_url": urls.get("download_url"),
                    }
                )

            return success_response(
                data={
                    "business_reference": reference,
                    "correlation_id": reference,
                    "count": len(history_items),
                    "security": security_context,
                    "history": history_items,
                },
                message="Generation history fetched successfully.",
            )
        except BaseApplicationException as exc:
            return self._error(exc)
