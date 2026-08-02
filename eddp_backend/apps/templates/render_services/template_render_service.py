from __future__ import annotations

import logging
import time
from typing import Any

from rest_framework import status

from apps.common.exceptions import ExternalServiceException, ResourceNotFoundException, ValidationException

from .base64_encoder import Base64Encoder
from .html2pdf_renderer import Html2PdfRenderer
from .html_generator import HtmlGenerator
from .response_builder import ResponseBuilder
from .template_resolver import TemplateResolver
from .variable_resolver import VariableResolver
from .version_resolver import VersionResolver

logger = logging.getLogger(__name__)


class TemplateRenderService:
    def __init__(
        self,
        *,
        template_resolver: TemplateResolver | None = None,
        version_resolver: VersionResolver | None = None,
        variable_resolver: VariableResolver | None = None,
        html_generator: HtmlGenerator | None = None,
        html2pdf_renderer: Html2PdfRenderer | None = None,
        base64_encoder: Base64Encoder | None = None,
        response_builder: ResponseBuilder | None = None,
    ) -> None:
        self.template_resolver = template_resolver or TemplateResolver()
        self.version_resolver = version_resolver or VersionResolver()
        self.variable_resolver = variable_resolver or VariableResolver()
        self.html_generator = html_generator or HtmlGenerator()
        self.html2pdf_renderer = html2pdf_renderer or Html2PdfRenderer()
        self.base64_encoder = base64_encoder or Base64Encoder()
        self.response_builder = response_builder or ResponseBuilder()

    @staticmethod
    def _as_json_safe(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): TemplateRenderService._as_json_safe(v) for k, v in value.items()}
        if isinstance(value, list):
            return [TemplateRenderService._as_json_safe(item) for item in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    def _log_request(
        self,
        *,
        template_code: str,
        template_version: str,
        payload: dict[str, Any],
        file_size: int,
        execution_ms: int,
        status_text: str,
        exception_message: str,
        user: Any,
    ) -> None:
        username = "System"
        if user is not None and getattr(user, "is_authenticated", False):
            username = str(getattr(user, "username", "System") or "System")

        log_record = {
            "event": "template_render",
            "template_code": template_code,
            "template_version": template_version,
            "request_payload": self._as_json_safe(payload),
            "generated_file_size": int(max(file_size, 0)),
            "execution_time_ms": int(max(execution_ms, 0)),
            "status": status_text,
            "exception": exception_message,
            "user": username,
            "timestamp": int(time.time()),
        }
        logger.info("template_render", extra={"template_render": log_record})

    def render(
        self,
        *,
        template_code: str,
        payload: dict[str, Any],
        output_format: str,
        response_type: str,
        user: Any,
    ) -> tuple[dict[str, Any], int]:
        started = time.perf_counter()
        file_size = 0
        template_version_name = ""

        try:
            if str(output_format).lower() != "pdf":
                raise ValidationException(detail="Only PDF output format is supported.")
            if str(response_type).lower() != "base64":
                raise ValidationException(detail="Only base64 response type is supported.")

            template = self.template_resolver.resolve(template_code)
            template_version = self.version_resolver.resolve_latest_approved(template)
            template_version_name = template_version.version_name

            missing = self.variable_resolver.find_missing_variables(template_version, payload)
            if missing:
                response = self.response_builder.missing_variables(missing)
                execution_ms = int((time.perf_counter() - started) * 1000)
                self._log_request(
                    template_code=template_code,
                    template_version=template_version_name,
                    payload=payload,
                    file_size=0,
                    execution_ms=execution_ms,
                    status_text="FAILED",
                    exception_message="",
                    user=user,
                )
                return response, status.HTTP_400_BAD_REQUEST

            html_result = self.html_generator.generate(
                template=template,
                template_version=template_version,
                payload=payload,
            )

            additional_missing = [token for token in html_result.get("missing_variables", []) if token not in missing]
            if additional_missing:
                response = self.response_builder.missing_variables(sorted(set(missing).union(additional_missing)))
                execution_ms = int((time.perf_counter() - started) * 1000)
                self._log_request(
                    template_code=template_code,
                    template_version=template_version_name,
                    payload=payload,
                    file_size=0,
                    execution_ms=execution_ms,
                    status_text="FAILED",
                    exception_message="",
                    user=user,
                )
                return response, status.HTTP_400_BAD_REQUEST

            pdf_bytes = self.html2pdf_renderer.render(html_result["html"])
            file_size = len(pdf_bytes)
            encoded = self.base64_encoder.encode(pdf_bytes)
            response = self.response_builder.success(
                template_code=template.code,
                template_name=template.name,
                content_base64=encoded,
            )

            execution_ms = int((time.perf_counter() - started) * 1000)
            self._log_request(
                template_code=template.code,
                template_version=template_version_name,
                payload=payload,
                file_size=file_size,
                execution_ms=execution_ms,
                status_text="SUCCESS",
                exception_message="",
                user=user,
            )
            return response, status.HTTP_200_OK

        except ResourceNotFoundException:
            response = self.response_builder.template_not_found()
            execution_ms = int((time.perf_counter() - started) * 1000)
            self._log_request(
                template_code=template_code,
                template_version=template_version_name,
                payload=payload,
                file_size=0,
                execution_ms=execution_ms,
                status_text="FAILED",
                exception_message="Template not found.",
                user=user,
            )
            return response, status.HTTP_404_NOT_FOUND

        except ValidationException as exc:
            detail = str(getattr(exc, "detail", "") or "")
            if "No approved template version available" in detail:
                response = self.response_builder.no_approved_version()
                status_code = status.HTTP_400_BAD_REQUEST
            elif "Missing runtime variable values for" in detail:
                # Defensive fallback in case missing-variable validation surfaces from lower layers.
                missing_raw = detail.split("for:", 1)[-1].split(".", 1)[0]
                missing = [item.strip() for item in missing_raw.split(",") if item.strip()]
                response = self.response_builder.missing_variables(missing)
                status_code = status.HTTP_400_BAD_REQUEST
            else:
                response = self.response_builder.rendering_failure()
                status_code = status.HTTP_400_BAD_REQUEST

            execution_ms = int((time.perf_counter() - started) * 1000)
            self._log_request(
                template_code=template_code,
                template_version=template_version_name,
                payload=payload,
                file_size=0,
                execution_ms=execution_ms,
                status_text="FAILED",
                exception_message=detail,
                user=user,
            )
            return response, status_code

        except ExternalServiceException as exc:
            response = self.response_builder.rendering_failure()
            execution_ms = int((time.perf_counter() - started) * 1000)
            self._log_request(
                template_code=template_code,
                template_version=template_version_name,
                payload=payload,
                file_size=0,
                execution_ms=execution_ms,
                status_text="FAILED",
                exception_message=str(getattr(exc, "detail", "") or str(exc)),
                user=user,
            )
            return response, status.HTTP_502_BAD_GATEWAY

        except Exception as exc:
            response = self.response_builder.rendering_failure()
            execution_ms = int((time.perf_counter() - started) * 1000)
            self._log_request(
                template_code=template_code,
                template_version=template_version_name,
                payload=payload,
                file_size=0,
                execution_ms=execution_ms,
                status_text="FAILED",
                exception_message=str(exc),
                user=user,
            )
            return response, status.HTTP_500_INTERNAL_SERVER_ERROR
