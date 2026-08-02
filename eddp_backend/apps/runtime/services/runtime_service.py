from __future__ import annotations

from typing import Any

from django.forms.models import model_to_dict
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from apps.common.exceptions import (
    BaseApplicationException,
    DuplicateResourceException,
    ResourceNotFoundException,
    ValidationException,
)
from apps.common.responses import error_response, success_response

from ..repositories import RuntimeEngineRepository, RuntimeRepository
from .connector_engine import ConnectorExecutionService
from .docx_generator import DOCXGeneratorService
from .html_builder import HTMLBuilderService
from .pdf_generator import PDFGeneratorService
from .rule_engine import RuleExecutionService
from .template_renderer import TemplateRenderingService
from .variable_resolver import VariableResolverService


class RuntimeService:
    """Service layer for Runtime aggregate operations."""

    def __init__(
        self,
        repository: RuntimeRepository | None = None,
        engine_repository: RuntimeEngineRepository | None = None,
        variable_resolver_service: VariableResolverService | None = None,
        rule_execution_service: RuleExecutionService | None = None,
        connector_execution_service: ConnectorExecutionService | None = None,
        template_rendering_service: TemplateRenderingService | None = None,
        html_builder_service: HTMLBuilderService | None = None,
        pdf_generator_service: PDFGeneratorService | None = None,
        docx_generator_service: DOCXGeneratorService | None = None,
    ) -> None:
        self.repository = repository or RuntimeRepository()
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

    @staticmethod
    def _serialize(instance: Any) -> dict[str, Any]:
        data = model_to_dict(instance)
        data["id"] = str(instance.id)
        data["code"] = instance.code
        data["status"] = instance.status
        data["is_deleted"] = instance.is_deleted
        data["created_at"] = instance.created_at.isoformat() if instance.created_at else None
        data["updated_at"] = instance.updated_at.isoformat() if instance.updated_at else None
        data["deleted_at"] = instance.deleted_at.isoformat() if instance.deleted_at else None
        return data

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

    def _get_instance_or_raise(self, id: Any):
        if not id:
            raise ValidationException(detail="Field 'id' is required.")
        instance = self.repository.get_by_id(id)
        if not instance:
            raise ResourceNotFoundException(detail="Resource not found.")
        return instance

    def _get_generation_request_or_raise(self, generation_request_id: Any):
        if not generation_request_id:
            raise ValidationException(detail="generation_request_id is required.")
        generation_request = self.engine_repository.get_generation_request_by_id(generation_request_id)
        if generation_request is None:
            raise ResourceNotFoundException(detail="Generation request not found.")
        return generation_request

    @staticmethod
    def _ensure_dict(value: Any, field_name: str) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValidationException(detail=f"{field_name} must be a JSON object.")
        return value

    def _prepare_rendering_context(
        self,
        data: dict[str, Any],
        *,
        require_generation_request: bool,
    ) -> dict[str, Any]:
        generation_request_id = data.get("generation_request_id")
        generation_request = None
        runtime_context = None

        if generation_request_id:
            generation_request = self._get_generation_request_or_raise(generation_request_id)
            runtime_context = self.engine_repository.get_runtime_context_by_generation_request(
                generation_request
            )
        elif require_generation_request:
            raise ValidationException(detail="generation_request_id is required.")

        variables: dict[str, Any] = {}
        if runtime_context is not None and isinstance(runtime_context.resolved_variables, dict):
            variables.update(runtime_context.resolved_variables)

        payload_variables = self._ensure_dict(data.get("variables") or {}, "variables")
        variables.update(payload_variables)

        if runtime_context is not None and isinstance(runtime_context.connector_response, dict):
            variables.setdefault("connector_response", runtime_context.connector_response)

        template_code = (data.get("template_code") or "").strip()
        template_version_code = (data.get("template_version_code") or "").strip()
        template_version_id = data.get("template_version_id")

        if not any([template_code, template_version_code, template_version_id]) and generation_request is not None:
            template_version_id = generation_request.template_version_id

        if not any([template_code, template_version_code, template_version_id]):
            raise ValidationException(
                detail=(
                    "One of template_code, template_version_code, template_version_id, "
                    "or generation_request_id is required."
                )
            )

        render_options = self._ensure_dict(data.get("render_options") or data.get("options") or {}, "render_options")
        layout_options = self._ensure_dict(data.get("layout_options") or {}, "layout_options")

        style_overrides = data.get("style_overrides") or ""
        if style_overrides and not isinstance(style_overrides, str):
            raise ValidationException(detail="style_overrides must be a string.")

        return {
            "generation_request": generation_request,
            "template_code": template_code,
            "template_version_code": template_version_code,
            "template_version_id": template_version_id,
            "variables": variables,
            "render_options": render_options,
            "layout_options": layout_options,
            "style_overrides": style_overrides,
        }

    def _persist_runtime_logs(
        self,
        *,
        generation_request,
        log_entries: list[dict[str, Any]],
    ) -> None:
        if generation_request is None or not log_entries:
            return
        self.engine_repository.upsert_runtime_context(
            generation_request=generation_request,
            execution_log_entries=log_entries,
        )

    def get_all(self) -> Response:
        try:
            records = [self._serialize(item) for item in self.repository.get_all()]
            return success_response(data=records, message="Records fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def get_by_id(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            return success_response(data=self._serialize(instance), message="Record fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def get_by_code(self, code: str) -> Response:
        try:
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            instance = self.repository.get_by_code(code)
            if not instance:
                raise ResourceNotFoundException(detail="Resource not found.")
            return success_response(data=self._serialize(instance), message="Record fetched successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def create(self, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            code = data.get("code")
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            if self.repository.exists(code):
                raise DuplicateResourceException(detail=f"Resource with code '{code}' already exists.")
            instance = self.repository.create(data)
            return success_response(
                data=self._serialize(instance),
                message="Record created successfully.",
                status_code=status.HTTP_201_CREATED,
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def update(self, id: Any, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            instance = self._get_instance_or_raise(id)
            new_code = data.get("code")
            if new_code:
                existing = self.repository.get_by_code(new_code)
                if existing and existing.id != instance.id:
                    raise DuplicateResourceException(detail=f"Resource with code '{new_code}' already exists.")
            updated = self.repository.update(instance, data)
            return success_response(data=self._serialize(updated), message="Record updated successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def soft_delete(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            deleted = self.repository.soft_delete(instance)
            return success_response(data=self._serialize(deleted), message="Record deleted successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def delete(self, id: Any) -> Response:
        return self.soft_delete(id)

    def restore(self, id: Any) -> Response:
        try:
            instance = self._get_instance_or_raise(id)
            restored = self.repository.restore(instance)
            return success_response(data=self._serialize(restored), message="Record restored successfully.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def exists(self, code: str) -> Response:
        try:
            if not code:
                raise ValidationException(detail="Field 'code' is required.")
            return success_response(data={"exists": self.repository.exists(code)}, message="Lookup completed.")
        except BaseApplicationException as exc:
            return self._error(exc)

    def resolve_variables(self, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            variable_group_code = (data.get("variable_group_code") or "").strip()
            if not variable_group_code:
                raise ValidationException(detail="variable_group_code is required.")

            resolution_result = self.variable_resolver_service.resolve_variables(
                variable_group_code=variable_group_code,
                runtime_payload=data.get("runtime_payload") or {},
                database_values=data.get("database_values") or {},
                connector_values=data.get("connector_values") or {},
                computed_values=data.get("computed_values") or {},
            )

            generation_request_id = data.get("generation_request_id")
            if generation_request_id:
                generation_request = self._get_generation_request_or_raise(generation_request_id)
                self.engine_repository.upsert_runtime_context(
                    generation_request=generation_request,
                    resolved_variables=resolution_result.get("resolved_variables", {}),
                    validation_results=resolution_result.get("validation_results", {}),
                    execution_log_entries=resolution_result.get("execution_log", []),
                )
                resolution_result["generation_request_id"] = str(generation_request.id)

            return success_response(
                data=resolution_result,
                message="Variables resolved successfully.",
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def execute_rules(self, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            rule_group_code = (data.get("rule_group_code") or "").strip()
            if not rule_group_code:
                raise ValidationException(detail="rule_group_code is required.")

            runtime_context = data.get("runtime_context") or {}
            if not runtime_context and isinstance(data.get("resolved_variables"), dict):
                runtime_context = {
                    "resolved_variables": data.get("resolved_variables") or {},
                    "variables": data.get("resolved_variables") or {},
                    "connector_response": data.get("connector_response") or {},
                }

            execution_result = self.rule_execution_service.execute_rules(
                rule_group_code=rule_group_code,
                runtime_context=runtime_context,
                stop_on_critical_failure=bool(data.get("stop_on_critical_failure", True)),
            )

            generation_request_id = data.get("generation_request_id")
            if generation_request_id:
                generation_request = self._get_generation_request_or_raise(generation_request_id)
                self.engine_repository.upsert_runtime_context(
                    generation_request=generation_request,
                    executed_rules=execution_result.get("executed_rules", []),
                    validation_results=execution_result.get("validation_results", {}),
                    execution_log_entries=execution_result.get("execution_log", []),
                    connector_response=(
                        runtime_context.get("connector_response")
                        if isinstance(runtime_context, dict)
                        else {}
                    ),
                )
                execution_result["generation_request_id"] = str(generation_request.id)

            return success_response(
                data=execution_result,
                message="Rules executed successfully.",
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def execute_connector(self, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            connector_code = (data.get("connector_code") or "").strip()
            if not connector_code:
                raise ValidationException(detail="connector_code is required.")

            generation_request = None
            runtime_context = None
            generation_request_id = data.get("generation_request_id")
            if generation_request_id:
                generation_request = self._get_generation_request_or_raise(generation_request_id)
                runtime_context = self.engine_repository.get_runtime_context_by_generation_request(
                    generation_request
                )

            base_context: dict[str, Any] = {}
            if runtime_context is not None:
                base_context = {
                    "resolved_variables": runtime_context.resolved_variables or {},
                    "variables": runtime_context.resolved_variables or {},
                    "executed_rules": runtime_context.executed_rules or [],
                    "validation_results": runtime_context.validation_results or {},
                    "connector_response": runtime_context.connector_response or {},
                }

            provided_context = data.get("context") or {}
            if not isinstance(provided_context, dict):
                raise ValidationException(detail="context must be a JSON object.")

            execution_context = {**base_context, **provided_context}
            connector_result = self.connector_execution_service.execute_connector(
                connector_code=connector_code,
                payload=data.get("payload") or {},
                operation=(data.get("operation") or "").strip(),
                context=execution_context,
                perform_validation=bool(data.get("perform_validation", True)),
            )

            if generation_request is not None:
                current_connector_response: dict[str, Any] = {}
                if runtime_context is not None and isinstance(runtime_context.connector_response, dict):
                    current_connector_response.update(runtime_context.connector_response)
                current_connector_response[connector_code] = connector_result.get("response", {})

                self.engine_repository.upsert_runtime_context(
                    generation_request=generation_request,
                    connector_response=current_connector_response,
                    execution_log_entries=connector_result.get("execution_log", []),
                )
                connector_result["generation_request_id"] = str(generation_request.id)

            return success_response(
                data=connector_result,
                message="Connector executed successfully.",
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def validate_connector(self, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            connector_code = (data.get("connector_code") or "").strip()
            if not connector_code:
                raise ValidationException(detail="connector_code is required.")

            validation_result = self.connector_execution_service.validate_connection(
                connector_code=connector_code,
                payload=data.get("payload") or {},
                operation=(data.get("operation") or "").strip(),
            )

            generation_request_id = data.get("generation_request_id")
            if generation_request_id:
                generation_request = self._get_generation_request_or_raise(generation_request_id)
                runtime_context = self.engine_repository.get_runtime_context_by_generation_request(
                    generation_request
                )

                validation_results: dict[str, Any] = {}
                if runtime_context is not None and isinstance(runtime_context.validation_results, dict):
                    validation_results.update(runtime_context.validation_results)

                connector_validations = validation_results.get("connector_validations")
                if not isinstance(connector_validations, dict):
                    connector_validations = {}
                connector_validations[connector_code] = validation_result
                validation_results["connector_validations"] = connector_validations

                self.engine_repository.upsert_runtime_context(
                    generation_request=generation_request,
                    validation_results=validation_results,
                    execution_log_entries=[
                        {
                            "timestamp": timezone.now().isoformat(),
                            "stage": "CONNECTOR_VALIDATION_ONLY",
                            "message": "Connector validation completed.",
                            "metadata": {
                                "connector_code": connector_code,
                                "result": validation_result,
                            },
                        }
                    ],
                )
                validation_result["generation_request_id"] = str(generation_request.id)

            return success_response(
                data=validation_result,
                message="Connector validation completed.",
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def render_template(self, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)

            generation_request = None
            runtime_context = None
            generation_request_id = data.get("generation_request_id")
            if generation_request_id:
                generation_request = self._get_generation_request_or_raise(generation_request_id)
                runtime_context = self.engine_repository.get_runtime_context_by_generation_request(
                    generation_request
                )

            variables: dict[str, Any] = {}
            if runtime_context is not None and isinstance(runtime_context.resolved_variables, dict):
                variables.update(runtime_context.resolved_variables)

            payload_variables = data.get("variables") or {}
            if not isinstance(payload_variables, dict):
                raise ValidationException(detail="variables must be a JSON object.")
            variables.update(payload_variables)

            if runtime_context is not None and isinstance(runtime_context.connector_response, dict):
                variables.setdefault("connector_response", runtime_context.connector_response)

            template_code = (data.get("template_code") or "").strip()
            template_version_code = (data.get("template_version_code") or "").strip()
            template_version_id = data.get("template_version_id")

            if not any([template_code, template_version_code, template_version_id]) and generation_request is not None:
                template_version_id = generation_request.template_version_id

            if not any([template_code, template_version_code, template_version_id]):
                raise ValidationException(
                    detail=(
                        "One of template_code, template_version_code, or template_version_id is required."
                    )
                )

            render_result = self.template_rendering_service.render_template(
                template_code=template_code,
                template_version_code=template_version_code,
                template_version_id=template_version_id,
                variables=variables,
                options=data.get("options") or {},
            )

            if generation_request is not None:
                self.engine_repository.upsert_runtime_context(
                    generation_request=generation_request,
                    execution_log_entries=render_result.get("execution_log", []),
                )
                render_result["generation_request_id"] = str(generation_request.id)

            return success_response(
                data=render_result,
                message="Template rendered successfully.",
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def build_html(self, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            rendering_context = self._prepare_rendering_context(
                data,
                require_generation_request=False,
            )

            generation_request = rendering_context["generation_request"]
            render_result = self.template_rendering_service.render_template(
                template_code=rendering_context["template_code"],
                template_version_code=rendering_context["template_version_code"],
                template_version_id=rendering_context["template_version_id"],
                variables=rendering_context["variables"],
                options=rendering_context["render_options"],
            )

            html_result = self.html_builder_service.build_html(
                template_name=render_result.get("template_name") or "Document",
                body_html=render_result.get("body_html") or "",
                header_html=render_result.get("header_html") or "",
                footer_html=render_result.get("footer_html") or "",
                variables=rendering_context["variables"],
                options=rendering_context["layout_options"],
                style_overrides=rendering_context["style_overrides"],
            )

            combined_log = [
                *(render_result.get("execution_log") or []),
                *(html_result.get("execution_log") or []),
            ]
            self._persist_runtime_logs(
                generation_request=generation_request,
                log_entries=combined_log,
            )

            response_data = {
                "template_code": render_result.get("template_code"),
                "template_name": render_result.get("template_name"),
                "template_version_code": render_result.get("template_version_code"),
                "template_version_number": render_result.get("template_version_number"),
                "html": html_result.get("html"),
                "page_size": html_result.get("page_size"),
                "orientation": html_result.get("orientation"),
                "execution_log": combined_log,
            }

            if generation_request is not None:
                response_data["generation_request_id"] = str(generation_request.id)

            return success_response(
                data=response_data,
                message="HTML built successfully.",
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def generate_pdf(self, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            rendering_context = self._prepare_rendering_context(
                data,
                require_generation_request=True,
            )

            generation_request = rendering_context["generation_request"]
            render_result = self.template_rendering_service.render_template(
                template_code=rendering_context["template_code"],
                template_version_code=rendering_context["template_version_code"],
                template_version_id=rendering_context["template_version_id"],
                variables=rendering_context["variables"],
                options=rendering_context["render_options"],
            )

            html_result = self.html_builder_service.build_html(
                template_name=render_result.get("template_name") or "Document",
                body_html=render_result.get("body_html") or "",
                header_html=render_result.get("header_html") or "",
                footer_html=render_result.get("footer_html") or "",
                variables=rendering_context["variables"],
                options=rendering_context["layout_options"],
                style_overrides=rendering_context["style_overrides"],
            )

            pdf_result = self.pdf_generator_service.generate_pdf(
                generation_request=generation_request,
                html_content=html_result.get("html") or "",
                file_name=(data.get("file_name") or ""),
            )

            combined_log = [
                *(render_result.get("execution_log") or []),
                *(html_result.get("execution_log") or []),
                *(pdf_result.get("execution_log") or []),
            ]
            self._persist_runtime_logs(
                generation_request=generation_request,
                log_entries=combined_log,
            )

            response_data = {
                "generation_request_id": str(generation_request.id),
                "template_code": render_result.get("template_code"),
                "template_version_code": render_result.get("template_version_code"),
                "page_size": html_result.get("page_size"),
                "orientation": html_result.get("orientation"),
                **pdf_result,
                "execution_log": combined_log,
            }

            return success_response(
                data=response_data,
                message="PDF generated successfully.",
                status_code=status.HTTP_201_CREATED,
            )
        except BaseApplicationException as exc:
            return self._error(exc)

    def generate_docx(self, data: dict[str, Any]) -> Response:
        try:
            self._validate_payload(data)
            rendering_context = self._prepare_rendering_context(
                data,
                require_generation_request=True,
            )

            generation_request = rendering_context["generation_request"]
            render_result = self.template_rendering_service.render_template(
                template_code=rendering_context["template_code"],
                template_version_code=rendering_context["template_version_code"],
                template_version_id=rendering_context["template_version_id"],
                variables=rendering_context["variables"],
                options=rendering_context["render_options"],
            )

            html_result = self.html_builder_service.build_html(
                template_name=render_result.get("template_name") or "Document",
                body_html=render_result.get("body_html") or "",
                header_html=render_result.get("header_html") or "",
                footer_html=render_result.get("footer_html") or "",
                variables=rendering_context["variables"],
                options=rendering_context["layout_options"],
                style_overrides=rendering_context["style_overrides"],
            )

            docx_result = self.docx_generator_service.generate_docx(
                generation_request=generation_request,
                html_content=html_result.get("body_html") or "",
                header_html=html_result.get("header_html") or "",
                footer_html=html_result.get("footer_html") or "",
                file_name=(data.get("file_name") or ""),
                document_title=render_result.get("template_name") or "Document",
            )

            combined_log = [
                *(render_result.get("execution_log") or []),
                *(html_result.get("execution_log") or []),
                *(docx_result.get("execution_log") or []),
            ]
            self._persist_runtime_logs(
                generation_request=generation_request,
                log_entries=combined_log,
            )

            response_data = {
                "generation_request_id": str(generation_request.id),
                "template_code": render_result.get("template_code"),
                "template_version_code": render_result.get("template_version_code"),
                **docx_result,
                "execution_log": combined_log,
            }

            return success_response(
                data=response_data,
                message="DOCX generated successfully.",
                status_code=status.HTTP_201_CREATED,
            )
        except BaseApplicationException as exc:
            return self._error(exc)
