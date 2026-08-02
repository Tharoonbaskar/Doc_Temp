from __future__ import annotations

from time import perf_counter
from typing import Any

from django.conf import settings
from django.utils import timezone

from apps.common.choices import OutputFormatChoices
from apps.common.exceptions import ExternalServiceException, ValidationException

from ..models import GenerationRequest
from ..repositories import RuntimeEngineRepository
from .file_storage import FileStorageService


class PDFGeneratorService:
    def __init__(
        self,
        repository: RuntimeEngineRepository | None = None,
        file_storage_service: FileStorageService | None = None,
    ) -> None:
        self.repository = repository or RuntimeEngineRepository()
        self.file_storage_service = file_storage_service or FileStorageService()

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
    def _normalize_file_name(file_name: str, generation_request: GenerationRequest) -> str:
        candidate = str(file_name or "").strip()
        if not candidate:
            candidate = f"{generation_request.code}-{timezone.now().strftime('%Y%m%d%H%M%S')}.pdf"
        if not candidate.lower().endswith(".pdf"):
            candidate = f"{candidate}.pdf"
        return candidate

    @staticmethod
    def _render_pdf_bytes(html_content: str) -> bytes:
        try:
            from xhtml2pdf import pisa
        except ImportError as exc:
            raise ExternalServiceException(
                detail=(
                    "xhtml2pdf is not installed. "
                    "Install it with: pip install xhtml2pdf"
                )
            ) from exc

        from io import BytesIO
        output = BytesIO()
        
        # Configure xhtml2pdf options for better rendering.
        # Convert HTML to PDF with proper encoding.
        pisa_status = pisa.CreatePDF(
            src=html_content,
            dest=output,
            encoding='UTF-8',
            xhtml=False  # Don't require strict XHTML
        )
        
        if pisa_status.err:
            raise ExternalServiceException(
                detail=f"PDF rendering failed with {pisa_status.err} errors."
            )
        
        return output.getvalue()

    def generate_pdf(
        self,
        *,
        generation_request: GenerationRequest,
        html_content: str,
        file_name: str = "",
    ) -> dict[str, Any]:
        if generation_request is None:
            raise ValidationException(detail="generation_request is required for PDF generation.")
        if not isinstance(html_content, str) or not html_content.strip():
            raise ValidationException(detail="html_content is required for PDF generation.")

        execution_log: list[dict[str, Any]] = []
        started_at = perf_counter()
        target_file_name = self._normalize_file_name(file_name, generation_request)

        self._log(
            execution_log,
            stage="PDF_GENERATION_START",
            message="PDF generation started.",
            metadata={"file_name": target_file_name},
        )

        try:
            pdf_bytes = self._render_pdf_bytes(html_content)
        except Exception as exc:
            raise ExternalServiceException(detail=f"PDF generation failed: {exc}") from exc

        storage_result = self.file_storage_service.save_bytes(
            content=pdf_bytes,
            file_name=target_file_name,
            subdirectory="generated-documents/pdf",
        )

        generated_document = self.repository.upsert_generated_document(
            generation_request=generation_request,
            file_name=storage_result["file_name"],
            file_path=storage_result["relative_path"],
            file_type=OutputFormatChoices.PDF,
            file_size=storage_result["file_size"],
            checksum=storage_result["checksum"],
        )

        duration_ms = round((perf_counter() - started_at) * 1000, 3)
        self._log(
            execution_log,
            stage="PDF_GENERATION_COMPLETE",
            message="PDF generation completed.",
            metadata={
                "file_size": storage_result["file_size"],
                "duration_ms": duration_ms,
                "storage_backend": storage_result["storage_backend"],
            },
        )

        return {
            "generated_document_id": str(generated_document.id),
            "generated_document_code": generated_document.code,
            "file_name": generated_document.file_name,
            "file_path": generated_document.file_path,
            "file_type": generated_document.file_type,
            "file_size": generated_document.file_size,
            "checksum": generated_document.checksum,
            "storage_backend": storage_result["storage_backend"],
            "duration_ms": duration_ms,
            "execution_log": execution_log,
        }
