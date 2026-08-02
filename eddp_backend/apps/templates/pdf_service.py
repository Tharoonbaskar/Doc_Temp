from __future__ import annotations

import base64
import json
import time
import uuid
from typing import Any

from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from apps.common.choices import StatusChoices, TemplateStatusChoices, VersionStatusChoices
from apps.common.exceptions import BaseApplicationException, ExternalServiceException, ResourceNotFoundException, ValidationException
from apps.common.responses import error_response, success_response
from apps.governance.models import ActivityLog, AuditLog
from apps.runtime.services.file_storage import FileStorageService

from .models import Template, TemplateVersion
from .pdf_engine import EnterprisePDFEngine


class TemplatePDFService:
    """Template-scoped enterprise PDF orchestration."""

    def __init__(
        self,
        *,
        pdf_engine: EnterprisePDFEngine | None = None,
        file_storage_service: FileStorageService | None = None,
    ) -> None:
        self.pdf_engine = pdf_engine or EnterprisePDFEngine()
        self.file_storage_service = file_storage_service or FileStorageService()

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
    def _normalize_dict(value: Any, field_name: str) -> dict[str, Any]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValidationException(detail=f"{field_name} must be a JSON object.")
        return value

    @staticmethod
    def _normalize_file_name(candidate: str, *, template_code: str, version_name: str) -> str:
        normalized = str(candidate or "").strip()
        if not normalized:
            normalized = f"{template_code}-{version_name}-{uuid.uuid4().hex[:8]}.pdf"
        if not normalized.lower().endswith(".pdf"):
            normalized = f"{normalized}.pdf"
        return normalized

    @staticmethod
    def _is_authenticated(user: Any) -> bool:
        return bool(user is not None and getattr(user, "is_authenticated", False))

    @staticmethod
    def _code(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"

    def _record_audit(
        self,
        *,
        action: str,
        template: Template,
        template_version: TemplateVersion,
        request,
        generated_by: str,
        duration_ms: int,
        variable_resolution_status: str,
        output_size_bytes: int,
        success: bool,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        user = getattr(request, "user", None) if request is not None else None
        performed_by = user if self._is_authenticated(user) else None

        xff = request.META.get("HTTP_X_FORWARDED_FOR", "") if request is not None else ""
        ip_address = xff.split(",")[0].strip() if xff else (
            request.META.get("REMOTE_ADDR", "") if request is not None else ""
        )
        user_agent = request.META.get("HTTP_USER_AGENT", "")[:512] if request is not None else ""

        payload = {
            "template_id": str(template.id),
            "template_code": template.code,
            "template_name": template.name,
            "template_version_id": str(template_version.id),
            "template_version": template_version.version_name,
            "generated_by": generated_by,
            "timestamp": timezone.now().isoformat(),
            "duration_ms": int(max(duration_ms, 0)),
            "variable_resolution_status": variable_resolution_status,
            "output_size_bytes": int(max(output_size_bytes, 0)),
            "success": bool(success),
            "details": extra or {},
        }

        try:
            audit_log = AuditLog.objects.create(
                code=self._code("TPDF-AUD"),
                entity_name="Template",
                entity_id=str(template.id),
                action=action,
                old_value={},
                new_value=payload,
                performed_by=performed_by,
                ip_address=ip_address or None,
                user_agent=user_agent,
                status=StatusChoices.ACTIVE,
                created_by=performed_by,
                updated_by=performed_by,
            )

            activity_log = ActivityLog.objects.create(
                code=self._code("TPDF-ACT"),
                module="TEMPLATES",
                activity=action,
                reference_number=template.code,
                description=(
                    f"{action}: template={template.code} version={template_version.version_name} "
                    f"success={success} duration_ms={duration_ms}"
                ),
                performed_by=performed_by,
                status=StatusChoices.ACTIVE,
                created_by=performed_by,
                updated_by=performed_by,
            )

            return {
                "audit_log_id": str(audit_log.id),
                "activity_log_id": str(activity_log.id),
            }
        except Exception:
            return {}

    def _get_template_or_raise(self, template_id: Any) -> Template:
        template = Template.objects.select_related("document").filter(id=template_id).first()
        if template is None:
            raise ResourceNotFoundException(detail="Template not found.")
        return template

    def _ensure_template_is_downloadable(self, template: Template) -> None:
        if template.status != TemplateStatusChoices.APPROVED:
            raise ValidationException(
                detail=(
                    "Only APPROVED templates can be used for PDF download. "
                    "Draft, For Review, and Rejected templates are blocked."
                )
            )

    def _resolve_approved_version(self, template: Template, version_selector: str = "") -> TemplateVersion:
        approved_versions = TemplateVersion.objects.filter(
            template=template,
            version_status=VersionStatusChoices.APPROVED,
        ).order_by("-version_number", "-approved_at", "-updated_at")

        if not approved_versions.exists():
            raise ValidationException(detail="No approved template version is available for PDF generation.")

        selector = str(version_selector or "").strip()
        if not selector:
            return approved_versions.first()

        by_name = approved_versions.filter(version_name__iexact=selector).first()
        if by_name is not None:
            return by_name

        normalized = selector.lower().removeprefix("v")
        parts = normalized.split(".")
        if parts and parts[0].isdigit():
            version_number = int(parts[0])
            by_number = approved_versions.filter(version_number=version_number).first()
            if by_number is not None:
                return by_number

        by_code = approved_versions.filter(code__iexact=selector).first()
        if by_code is not None:
            return by_code

        raise ValidationException(detail=f"Approved template version '{selector}' was not found.")

    def _build_download_url(self, *, request, template_id: str, version_name: str) -> str:
        path = f"/api/templates/{template_id}/download-pdf?version={version_name}"
        if request is None:
            return path
        return request.build_absolute_uri(path)

    def _build_file_url(self, *, request, relative_path: str) -> str:
        path = f"{str(settings.MEDIA_URL).rstrip('/')}/{str(relative_path).lstrip('/')}"
        if request is None:
            return path
        return request.build_absolute_uri(path)

    def _generate_pdf_bundle(
        self,
        *,
        template: Template,
        template_version: TemplateVersion,
        payload: dict[str, Any],
        generated_by: str,
    ) -> dict[str, Any]:
        variables = self._normalize_dict(payload.get("variables") or {}, "variables")
        options = self._normalize_dict(payload.get("pdf_options") or {}, "pdf_options")
        metadata = self._normalize_dict(payload.get("metadata") or {}, "metadata")

        return self.pdf_engine.generate_document_pdf(
            template=template,
            template_version=template_version,
            variables=variables,
            options=options,
            metadata_overrides=metadata,
            generated_by=generated_by,
        )

    @staticmethod
    def _unexpected_error(exc: Exception) -> ExternalServiceException:
        return ExternalServiceException(detail=f"PDF processing failed: {exc}")

    def preview_pdf(self, *, request, template_id: Any, payload: dict[str, Any]) -> Response:
        started = time.perf_counter()
        template_version: TemplateVersion | None = None
        template: Template | None = None

        try:
            template = self._get_template_or_raise(template_id)
            self._ensure_template_is_downloadable(template)
            version_selector = str(payload.get("version") or "").strip()
            template_version = self._resolve_approved_version(template, version_selector)

            generated_by = (
                getattr(getattr(request, "user", None), "username", "")
                if self._is_authenticated(getattr(request, "user", None))
                else "System"
            )

            bundle = self._generate_pdf_bundle(
                template=template,
                template_version=template_version,
                payload=payload,
                generated_by=generated_by,
            )

            duration_ms = int((time.perf_counter() - started) * 1000)
            variable_status = "RESOLVED" if not bundle.get("missing_variables") else "UNRESOLVED_ALLOWED"
            audit_meta = self._record_audit(
                action="PREVIEW_TEMPLATE_PDF",
                template=template,
                template_version=template_version,
                request=request,
                generated_by=generated_by,
                duration_ms=duration_ms,
                variable_resolution_status=variable_status,
                output_size_bytes=len(bundle["pdf_bytes"]),
                success=True,
                extra={"mode": "preview", "warnings": bundle.get("warnings", [])},
            )

            return success_response(
                data={
                    "template_name": template.name,
                    "template_code": template.code,
                    "approved_version": template_version.version_name,
                    "status": template.status,
                    "generated_date": timezone.now().isoformat(),
                    "generated_by": generated_by,
                    "page_count": bundle.get("page_count", 0),
                    "preview_base64": base64.b64encode(bundle["pdf_bytes"]).decode("ascii"),
                    "mime_type": "application/pdf",
                    "missing_variables": bundle.get("missing_variables", []),
                    "warnings": bundle.get("warnings", []),
                    "metadata": bundle.get("metadata", {}),
                    "options": bundle.get("options", {}),
                    "audit": audit_meta,
                },
                message="Template PDF preview generated successfully.",
            )
        except BaseApplicationException as exc:
            if template is not None and template_version is not None:
                duration_ms = int((time.perf_counter() - started) * 1000)
                self._record_audit(
                    action="PREVIEW_TEMPLATE_PDF",
                    template=template,
                    template_version=template_version,
                    request=request,
                    generated_by=(
                        getattr(getattr(request, "user", None), "username", "System")
                        if request is not None
                        else "System"
                    ),
                    duration_ms=duration_ms,
                    variable_resolution_status="FAILED",
                    output_size_bytes=0,
                    success=False,
                    extra={"error": str(exc.detail)},
                )
            return self._error(exc)
        except Exception as exc:
            wrapped = self._unexpected_error(exc)
            if template is not None and template_version is not None:
                duration_ms = int((time.perf_counter() - started) * 1000)
                self._record_audit(
                    action="PREVIEW_TEMPLATE_PDF",
                    template=template,
                    template_version=template_version,
                    request=request,
                    generated_by=(
                        getattr(getattr(request, "user", None), "username", "System")
                        if request is not None
                        else "System"
                    ),
                    duration_ms=duration_ms,
                    variable_resolution_status="FAILED",
                    output_size_bytes=0,
                    success=False,
                    extra={"error": str(exc)},
                )
            return self._error(wrapped)

    def generate_pdf(self, *, request, template_id: Any, payload: dict[str, Any]) -> Response:
        started = time.perf_counter()
        template_version: TemplateVersion | None = None
        template: Template | None = None

        try:
            template = self._get_template_or_raise(template_id)
            self._ensure_template_is_downloadable(template)
            version_selector = str(payload.get("version") or "").strip()
            template_version = self._resolve_approved_version(template, version_selector)

            generated_by = (
                getattr(getattr(request, "user", None), "username", "")
                if self._is_authenticated(getattr(request, "user", None))
                else "System"
            )

            bundle = self._generate_pdf_bundle(
                template=template,
                template_version=template_version,
                payload=payload,
                generated_by=generated_by,
            )

            file_name = self._normalize_file_name(
                str(payload.get("file_name") or ""),
                template_code=template.code,
                version_name=template_version.version_name,
            )
            storage = self.file_storage_service.save_bytes(
                content=bundle["pdf_bytes"],
                file_name=file_name,
                subdirectory=f"generated-template-pdfs/{template.code.lower()}",
            )

            duration_ms = int((time.perf_counter() - started) * 1000)
            variable_status = "RESOLVED" if not bundle.get("missing_variables") else "UNRESOLVED_ALLOWED"
            audit_meta = self._record_audit(
                action="GENERATE_TEMPLATE_PDF",
                template=template,
                template_version=template_version,
                request=request,
                generated_by=generated_by,
                duration_ms=duration_ms,
                variable_resolution_status=variable_status,
                output_size_bytes=storage.get("file_size", 0),
                success=True,
                extra={
                    "checksum": storage.get("checksum"),
                    "storage_backend": storage.get("storage_backend"),
                    "warnings": bundle.get("warnings", []),
                },
            )

            return success_response(
                data={
                    "template_name": template.name,
                    "template_code": template.code,
                    "approved_version": template_version.version_name,
                    "status": template.status,
                    "generated_date": timezone.now().isoformat(),
                    "generated_by": generated_by,
                    "page_count": bundle.get("page_count", 0),
                    "missing_variables": bundle.get("missing_variables", []),
                    "warnings": bundle.get("warnings", []),
                    "metadata": bundle.get("metadata", {}),
                    "options": bundle.get("options", {}),
                    "file_name": storage.get("file_name"),
                    "file_size": storage.get("file_size"),
                    "checksum": storage.get("checksum"),
                    "file_url": self._build_file_url(request=request, relative_path=storage.get("relative_path", "")),
                    "download_url": self._build_download_url(
                        request=request,
                        template_id=str(template.id),
                        version_name=template_version.version_name,
                    ),
                    "audit": audit_meta,
                },
                message="Template PDF generated successfully.",
                status_code=status.HTTP_201_CREATED,
            )
        except BaseApplicationException as exc:
            if template is not None and template_version is not None:
                duration_ms = int((time.perf_counter() - started) * 1000)
                self._record_audit(
                    action="GENERATE_TEMPLATE_PDF",
                    template=template,
                    template_version=template_version,
                    request=request,
                    generated_by=(
                        getattr(getattr(request, "user", None), "username", "System")
                        if request is not None
                        else "System"
                    ),
                    duration_ms=duration_ms,
                    variable_resolution_status="FAILED",
                    output_size_bytes=0,
                    success=False,
                    extra={"error": str(exc.detail)},
                )
            return self._error(exc)
        except Exception as exc:
            wrapped = self._unexpected_error(exc)
            if template is not None and template_version is not None:
                duration_ms = int((time.perf_counter() - started) * 1000)
                self._record_audit(
                    action="GENERATE_TEMPLATE_PDF",
                    template=template,
                    template_version=template_version,
                    request=request,
                    generated_by=(
                        getattr(getattr(request, "user", None), "username", "System")
                        if request is not None
                        else "System"
                    ),
                    duration_ms=duration_ms,
                    variable_resolution_status="FAILED",
                    output_size_bytes=0,
                    success=False,
                    extra={"error": str(exc)},
                )
            return self._error(wrapped)

    def _parse_download_variables(self, raw_value: str) -> dict[str, Any]:
        if not raw_value:
            return {}
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise ValidationException(detail=f"Invalid variables JSON: {exc}") from exc
        if not isinstance(parsed, dict):
            raise ValidationException(detail="variables query value must decode to a JSON object.")
        return parsed

    def _download_payload_from_query(self, query_params) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "version": str(query_params.get("version") or "").strip(),
            "variables": self._parse_download_variables(str(query_params.get("variables") or "").strip()),
            "pdf_options": {
                "variable_resolution_mode": str(
                    query_params.get("variable_resolution_mode") or "RESOLVE_STRICT"
                ).strip(),
            },
            "metadata": {},
        }

        watermark = str(query_params.get("watermark") or "").strip()
        if watermark:
            payload["pdf_options"]["watermark"] = watermark

        return payload

    def download_pdf(self, *, request, template_id: Any, query_params) -> Response | HttpResponse:
        started = time.perf_counter()
        template: Template | None = None
        template_version: TemplateVersion | None = None

        try:
            payload = self._download_payload_from_query(query_params)
            template = self._get_template_or_raise(template_id)
            self._ensure_template_is_downloadable(template)

            version_selector = str(payload.get("version") or "").strip()
            template_version = self._resolve_approved_version(template, version_selector)

            generated_by = (
                getattr(getattr(request, "user", None), "username", "")
                if self._is_authenticated(getattr(request, "user", None))
                else "System"
            )

            bundle = self._generate_pdf_bundle(
                template=template,
                template_version=template_version,
                payload=payload,
                generated_by=generated_by,
            )

            response = HttpResponse(bundle["pdf_bytes"], content_type="application/pdf")
            response["Content-Disposition"] = (
                f"attachment; filename={template.code}-{template_version.version_name}.pdf"
            )

            duration_ms = int((time.perf_counter() - started) * 1000)
            variable_status = "RESOLVED" if not bundle.get("missing_variables") else "UNRESOLVED_ALLOWED"
            self._record_audit(
                action="DOWNLOAD_TEMPLATE_PDF",
                template=template,
                template_version=template_version,
                request=request,
                generated_by=generated_by,
                duration_ms=duration_ms,
                variable_resolution_status=variable_status,
                output_size_bytes=len(bundle["pdf_bytes"]),
                success=True,
                extra={"mode": "direct-download", "warnings": bundle.get("warnings", [])},
            )

            return response
        except BaseApplicationException as exc:
            if template is not None and template_version is not None:
                duration_ms = int((time.perf_counter() - started) * 1000)
                self._record_audit(
                    action="DOWNLOAD_TEMPLATE_PDF",
                    template=template,
                    template_version=template_version,
                    request=request,
                    generated_by=(
                        getattr(getattr(request, "user", None), "username", "System")
                        if request is not None
                        else "System"
                    ),
                    duration_ms=duration_ms,
                    variable_resolution_status="FAILED",
                    output_size_bytes=0,
                    success=False,
                    extra={"error": str(exc.detail)},
                )
            return self._error(exc)
        except Exception as exc:
            wrapped = self._unexpected_error(exc)
            if template is not None and template_version is not None:
                duration_ms = int((time.perf_counter() - started) * 1000)
                self._record_audit(
                    action="DOWNLOAD_TEMPLATE_PDF",
                    template=template,
                    template_version=template_version,
                    request=request,
                    generated_by=(
                        getattr(getattr(request, "user", None), "username", "System")
                        if request is not None
                        else "System"
                    ),
                    duration_ms=duration_ms,
                    variable_resolution_status="FAILED",
                    output_size_bytes=0,
                    success=False,
                    extra={"error": str(exc)},
                )
            return self._error(wrapped)
