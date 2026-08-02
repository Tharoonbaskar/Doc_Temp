from __future__ import annotations

import uuid
from typing import Any

from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from apps.common.choices import StatusChoices
from apps.connectors.models import Connector, ConnectorConfiguration
from apps.documents.models import Document, DocumentDefinition
from apps.rules.models import Rule, RuleGroup
from apps.templates.models import Template, TemplateComponent, TemplateStyle, TemplateVersion
from apps.variables.models import Variable, VariableGroup

from .models import GeneratedDocument, GenerationRequest, RuntimeContext


class RuntimeRepository:
    model = GenerationRequest

    def get_all(self) -> QuerySet[GenerationRequest]:
        return self.model.objects.all()

    def get_by_id(self, id: Any) -> GenerationRequest | None:
        return self.model.objects.filter(id=id).first()

    def get_by_code(self, code: str) -> GenerationRequest | None:
        return self.model.objects.filter(code=code).first()

    @transaction.atomic
    def create(self, data: dict[str, Any]) -> GenerationRequest:
        return self.model.objects.create(**data)

    @transaction.atomic
    def update(self, instance: GenerationRequest, data: dict[str, Any]) -> GenerationRequest:
        for field, value in data.items():
            setattr(instance, field, value)
        if data:
            instance.save(update_fields=list(data.keys()))
        else:
            instance.save()
        return instance

    @transaction.atomic
    def soft_delete(self, instance: GenerationRequest) -> GenerationRequest:
        instance.soft_delete()
        return instance

    @transaction.atomic
    def restore(self, instance: GenerationRequest) -> GenerationRequest:
        instance.restore()
        return instance

    def exists(self, code: str) -> bool:
        return self.model.objects.filter(code=code).exists()


class RuntimeEngineRepository:
    generation_request_model = GenerationRequest
    runtime_context_model = RuntimeContext
    generated_document_model = GeneratedDocument

    @staticmethod
    def _context_code() -> str:
        return f"CTX-{uuid.uuid4().hex[:12].upper()}"

    @staticmethod
    def _generated_document_code() -> str:
        return f"GDOC-{uuid.uuid4().hex[:12].upper()}"

    def get_generation_request_by_id(self, generation_request_id: Any) -> GenerationRequest | None:
        return (
            self.generation_request_model.objects.filter(id=generation_request_id)
            .select_related(
                "document",
                "template_version",
                "template_version__template",
                "generated_document",
                "runtime_context",
            )
            .first()
        )

    def get_generation_request_by_request_id(self, request_id: Any) -> GenerationRequest | None:
        return (
            self.generation_request_model.objects.filter(request_id=request_id)
            .select_related(
                "document",
                "template_version",
                "template_version__template",
                "generated_document",
                "runtime_context",
            )
            .first()
        )

    @transaction.atomic
    def create_generation_request(self, data: dict[str, Any]) -> GenerationRequest:
        return self.generation_request_model.objects.create(**data)

    def get_document_by_id(self, document_id: Any) -> Document | None:
        return Document.objects.filter(id=document_id).first()

    def get_generation_requests_by_business_reference(
        self,
        business_reference: str,
    ) -> QuerySet[GenerationRequest]:
        return (
            self.generation_request_model.objects.filter(business_reference=business_reference)
            .select_related("document", "template_version", "generated_document")
            .order_by("-requested_at")
        )

    @transaction.atomic
    def update_generation_request_status(
        self,
        *,
        generation_request: GenerationRequest,
        status_value: str,
        completed: bool = False,
    ) -> GenerationRequest:
        generation_request.status = status_value
        update_fields = ["status"]

        if completed:
            completed_at = timezone.now()
            generation_request.completed_at = completed_at
            update_fields.append("completed_at")

            if generation_request.requested_at:
                delta = completed_at - generation_request.requested_at
                generation_request.processing_time_ms = int(delta.total_seconds() * 1000)
                update_fields.append("processing_time_ms")

        generation_request.save(update_fields=update_fields)
        return generation_request

    def get_runtime_context_by_generation_request(
        self,
        generation_request: GenerationRequest,
    ) -> RuntimeContext | None:
        return self.runtime_context_model.objects.filter(generation_request=generation_request).first()

    def get_generated_document_by_generation_request(
        self,
        generation_request: GenerationRequest,
    ) -> GeneratedDocument | None:
        return self.generated_document_model.objects.filter(generation_request=generation_request).first()

    @transaction.atomic
    def upsert_runtime_context(
        self,
        *,
        generation_request: GenerationRequest,
        resolved_variables: dict[str, Any] | None = None,
        executed_rules: list[dict[str, Any]] | None = None,
        validation_results: dict[str, Any] | None = None,
        connector_response: dict[str, Any] | None = None,
        execution_log_entries: list[dict[str, Any]] | None = None,
    ) -> RuntimeContext:
        context = self.get_runtime_context_by_generation_request(generation_request)
        creating = context is None

        if creating:
            context = self.runtime_context_model.objects.create(
                code=self._context_code(),
                generation_request=generation_request,
                resolved_variables=resolved_variables or {},
                executed_rules=executed_rules or [],
                validation_results=validation_results or {},
                connector_response=connector_response or {},
                execution_log=execution_log_entries or [],
                status=StatusChoices.ACTIVE,
            )
            return context

        update_fields: list[str] = []

        if resolved_variables is not None:
            context.resolved_variables = resolved_variables
            update_fields.append("resolved_variables")

        if executed_rules is not None:
            context.executed_rules = executed_rules
            update_fields.append("executed_rules")

        if validation_results is not None:
            context.validation_results = validation_results
            update_fields.append("validation_results")

        if connector_response is not None:
            context.connector_response = connector_response
            update_fields.append("connector_response")

        if execution_log_entries:
            current_log = list(context.execution_log or [])
            context.execution_log = current_log + execution_log_entries
            update_fields.append("execution_log")

        if update_fields:
            context.save(update_fields=update_fields)
        return context

    @transaction.atomic
    def upsert_generated_document(
        self,
        *,
        generation_request: GenerationRequest,
        file_name: str,
        file_path: str,
        file_type: str,
        file_size: int,
        checksum: str,
    ) -> GeneratedDocument:
        document = self.get_generated_document_by_generation_request(generation_request)
        if document is None:
            return self.generated_document_model.objects.create(
                code=self._generated_document_code(),
                generation_request=generation_request,
                file_name=file_name,
                file_path=file_path,
                file_type=file_type,
                file_size=file_size,
                checksum=checksum,
                status=StatusChoices.PUBLISHED,
            )

        document.file_name = file_name
        document.file_path = file_path
        document.file_type = file_type
        document.file_size = file_size
        document.checksum = checksum
        document.status = StatusChoices.PUBLISHED
        document.save(
            update_fields=[
                "file_name",
                "file_path",
                "file_type",
                "file_size",
                "checksum",
                "status",
            ]
        )
        return document

    def get_variable_group_by_code(self, variable_group_code: str) -> VariableGroup | None:
        return VariableGroup.objects.filter(code=variable_group_code).first()

    def get_variables_by_group(self, variable_group: VariableGroup) -> QuerySet[Variable]:
        return Variable.objects.filter(group=variable_group).order_by("name")

    def get_rule_group_by_code(self, rule_group_code: str) -> RuleGroup | None:
        return RuleGroup.objects.filter(code=rule_group_code).first()

    def get_rules_by_group(self, rule_group: RuleGroup) -> QuerySet[Rule]:
        return Rule.objects.filter(rule_group=rule_group, is_active=True).order_by("execution_order", "name")

    def get_document_definition_by_document_code(self, document_code: str) -> DocumentDefinition | None:
        return DocumentDefinition.objects.filter(document__code=document_code).select_related("document").first()

    def get_connector_by_code(self, connector_code: str) -> Connector | None:
        return Connector.objects.filter(code=connector_code, is_active=True).first()

    def get_connector_configuration(self, connector: Connector) -> ConnectorConfiguration | None:
        return ConnectorConfiguration.objects.filter(connector=connector).first()

    def get_template_by_code(self, template_code: str) -> Template | None:
        return Template.objects.filter(code=template_code).select_related("document").first()

    def get_default_template_for_document(self, document: Document) -> Template | None:
        default_template = (
            Template.objects.filter(document=document, is_default=True)
            .order_by("-updated_at")
            .first()
        )
        if default_template is not None:
            return default_template

        return Template.objects.filter(document=document).order_by("-updated_at").first()

    def get_template_version_by_code(self, template_version_code: str) -> TemplateVersion | None:
        return (
            TemplateVersion.objects.filter(code=template_version_code)
            .select_related("template", "template__document")
            .first()
        )

    def get_template_version_by_id(self, template_version_id: Any) -> TemplateVersion | None:
        return (
            TemplateVersion.objects.filter(id=template_version_id)
            .select_related("template", "template__document")
            .first()
        )

    def get_active_template_version(self, template: Template) -> TemplateVersion | None:
        return (
            TemplateVersion.objects.filter(template=template)
            .order_by("-published_at", "-version_number")
            .first()
        )

    def get_template_components(self, template_version: TemplateVersion) -> QuerySet[TemplateComponent]:
        return TemplateComponent.objects.filter(template_version=template_version).order_by(
            "display_order", "component_name"
        )

    def get_template_style(self, template_version: TemplateVersion) -> TemplateStyle | None:
        return TemplateStyle.objects.filter(template_version=template_version).first()