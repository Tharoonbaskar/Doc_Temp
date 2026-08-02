from __future__ import annotations

from typing import Any


class ResponseBuilder:
    @staticmethod
    def success(*, template_code: str, template_name: str, content_base64: str) -> dict[str, Any]:
        safe_name = (template_name or "DOCUMENT").strip().replace(" ", "_")
        if not safe_name:
            safe_name = "DOCUMENT"

        return {
            "status": "SUCCESS",
            "message": "Template rendered successfully.",
            "document": {
                "template_code": template_code,
                "template_name": template_name,
                "file_name": f"{safe_name}.pdf",
                "mime_type": "application/pdf",
                "content": content_base64,
            },
        }

    @staticmethod
    def missing_variables(missing_variables: list[str]) -> dict[str, Any]:
        return {
            "status": "FAILED",
            "message": "Required template variables are missing.",
            "missing_variables": missing_variables,
        }

    @staticmethod
    def template_not_found() -> dict[str, Any]:
        return {
            "status": "FAILED",
            "message": "Template not found.",
        }

    @staticmethod
    def no_approved_version() -> dict[str, Any]:
        return {
            "status": "FAILED",
            "message": "No approved template version available.",
        }

    @staticmethod
    def rendering_failure() -> dict[str, Any]:
        return {
            "status": "FAILED",
            "message": "Unable to generate PDF.",
        }
