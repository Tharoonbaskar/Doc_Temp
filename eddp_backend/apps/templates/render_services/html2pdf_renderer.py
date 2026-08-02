from __future__ import annotations

from apps.common.exceptions import ExternalServiceException

from ..pdf_engine import EnterprisePDFEngine


class Html2PdfRenderer:
    def __init__(self, pdf_engine: EnterprisePDFEngine | None = None) -> None:
        self.pdf_engine = pdf_engine or EnterprisePDFEngine()

    def render(self, html_document: str) -> bytes:
        try:
            return self.pdf_engine._render_pdf_bytes(html_document)
        except Exception as exc:
            raise ExternalServiceException(detail="Unable to generate PDF.") from exc
