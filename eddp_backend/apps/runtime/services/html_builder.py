from __future__ import annotations

import html
import json
import re
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

from apps.common.exceptions import ValidationException
from apps.common.validators import validate_json

_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.\[\]]+)\s*\}\}")
_PAGE_BREAK_MARKERS = [
    re.compile(r"<!--\s*PAGE_BREAK\s*-->", re.IGNORECASE),
    re.compile(r"\[\[\s*PAGE_BREAK\s*\]\]", re.IGNORECASE),
    re.compile(r"<\s*page-break\s*/\s*>", re.IGNORECASE),
    re.compile(r"<\s*page-break\s*>\s*<\s*/\s*page-break\s*>", re.IGNORECASE),
]
_TABLE_TAG_PATTERN = re.compile(r"<table([^>]*)>", re.IGNORECASE)
_IMAGE_TAG_PATTERN = re.compile(r"<img([^>]*)>", re.IGNORECASE)

_ALLOWED_PAGE_SIZES = {"A4", "LETTER"}
_ALLOWED_ORIENTATIONS = {"PORTRAIT", "LANDSCAPE"}


class HTMLBuilderService:
    """Builds print-ready HTML from rendered template fragments."""

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

    def _resolve_placeholders(self, value: str, variables: dict[str, Any]) -> str:
        if not isinstance(value, str) or "{{" not in value:
            return value

        def replace(match: re.Match[str]) -> str:
            reference = match.group(1)
            resolved = self._get_by_path(variables, reference)
            if resolved is None:
                return ""
            if isinstance(resolved, (dict, list)):
                resolved = json.dumps(resolved)
            return html.escape(str(resolved))

        return _PLACEHOLDER_PATTERN.sub(replace, value)

    @staticmethod
    def _normalize_page_size(options: dict[str, Any]) -> str:
        page_size = str(options.get("page_size") or "A4").strip().upper()
        if page_size not in _ALLOWED_PAGE_SIZES:
            supported = ", ".join(sorted(_ALLOWED_PAGE_SIZES))
            raise ValidationException(detail=f"Unsupported page_size '{page_size}'. Supported values: {supported}.")
        return page_size

    @staticmethod
    def _normalize_orientation(options: dict[str, Any]) -> str:
        orientation = str(options.get("orientation") or "PORTRAIT").strip().upper()
        if orientation not in _ALLOWED_ORIENTATIONS:
            supported = ", ".join(sorted(_ALLOWED_ORIENTATIONS))
            raise ValidationException(
                detail=f"Unsupported orientation '{orientation}'. Supported values: {supported}."
            )
        return orientation

    @staticmethod
    def _to_mm(value: Any, *, field_name: str, default: float) -> str:
        if value is None or value == "":
            value = default
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise ValidationException(detail=f"{field_name} must be a number.") from exc
        if numeric < 0:
            raise ValidationException(detail=f"{field_name} cannot be negative.")
        return f"{numeric:g}mm"

    @staticmethod
    def _apply_page_breaks(content: str) -> str:
        processed = content
        for marker in _PAGE_BREAK_MARKERS:
            processed = marker.sub('<div class="page-break"></div>', processed)
        return processed

    @staticmethod
    def _inject_class(attributes: str, class_name: str) -> str:
        attrs = attributes or ""
        class_match = re.search(r'class\s*=\s*"([^"]*)"', attrs, flags=re.IGNORECASE)
        if class_match:
            current_classes = class_match.group(1)
            classes = {token.strip() for token in current_classes.split(" ") if token.strip()}
            classes.add(class_name)
            replacement = f'class="{" ".join(sorted(classes))}"'
            return re.sub(r'class\s*=\s*"([^"]*)"', replacement, attrs, flags=re.IGNORECASE)
        return f'{attrs} class="{class_name}"'

    def _apply_table_support(self, content: str) -> str:
        def replace(match: re.Match[str]) -> str:
            attrs = self._inject_class(match.group(1) or "", "runtime-table")
            return f"<table{attrs}>"

        return _TABLE_TAG_PATTERN.sub(replace, content)

    def _apply_image_support(self, content: str) -> str:
        def replace(match: re.Match[str]) -> str:
            attrs = self._inject_class(match.group(1) or "", "runtime-image")
            if not re.search(r'loading\s*=\s*"[^"]*"', attrs, flags=re.IGNORECASE):
                attrs = f'{attrs} loading="lazy"'
            return f"<img{attrs}>"

        return _IMAGE_TAG_PATTERN.sub(replace, content)

    def _compose_styles(
        self,
        *,
        page_size: str,
        orientation: str,
        margin_top: str,
        margin_bottom: str,
        margin_left: str,
        margin_right: str,
        header_height: str,
        footer_height: str,
        style_overrides: str,
    ) -> str:
        return (
            "@page {"
            f" size: {page_size} {orientation.lower()};"
            f" margin-top: {margin_top};"
            f" margin-bottom: {margin_bottom};"
            f" margin-left: {margin_left};"
            f" margin-right: {margin_right};"
            " }"
            "html, body { margin: 0; padding: 0; }"
            "body { font-family: 'Segoe UI', Arial, sans-serif; font-size: 12px; color: #111; }"
            ".document-shell { width: 100%; }"
            ".document-header, .document-footer { position: fixed; left: 0; right: 0; width: 100%; }"
            ".document-header { top: 0; }"
            ".document-footer { bottom: 0; }"
            ".document-content {"
            f" padding-top: {header_height};"
            f" padding-bottom: {footer_height};"
            " }"
            ".runtime-table { border-collapse: collapse; width: 100%; margin: 8px 0; }"
            ".runtime-table th, .runtime-table td { border: 1px solid #505050; padding: 6px; text-align: left; }"
            ".runtime-image { max-width: 100%; height: auto; display: block; }"
            ".page-break { break-after: page; page-break-after: always; height: 0; }"
            f"{style_overrides}"
        )

    def build_html(
        self,
        *,
        template_name: str,
        body_html: str,
        header_html: str = "",
        footer_html: str = "",
        variables: Any = None,
        options: Any = None,
        style_overrides: str = "",
    ) -> dict[str, Any]:
        variables_dict = self._ensure_dict(variables, "variables")
        options_dict = self._ensure_dict(options, "options")

        page_size = self._normalize_page_size(options_dict)
        orientation = self._normalize_orientation(options_dict)

        margin_top = self._to_mm(options_dict.get("margin_top"), field_name="margin_top", default=12.0)
        margin_bottom = self._to_mm(options_dict.get("margin_bottom"), field_name="margin_bottom", default=12.0)
        margin_left = self._to_mm(options_dict.get("margin_left"), field_name="margin_left", default=12.0)
        margin_right = self._to_mm(options_dict.get("margin_right"), field_name="margin_right", default=12.0)
        header_height = self._to_mm(options_dict.get("header_height"), field_name="header_height", default=18.0)
        footer_height = self._to_mm(options_dict.get("footer_height"), field_name="footer_height", default=14.0)

        include_header = bool(options_dict.get("include_header", True))
        include_footer = bool(options_dict.get("include_footer", True))

        execution_log: list[dict[str, Any]] = []
        self._log(
            execution_log,
            stage="HTML_BUILD_START",
            message="HTML build started.",
            metadata={
                "page_size": page_size,
                "orientation": orientation,
                "include_header": include_header,
                "include_footer": include_footer,
            },
        )

        resolved_body = self._resolve_placeholders(body_html or "", variables_dict)
        resolved_header = self._resolve_placeholders(header_html or "", variables_dict)
        resolved_footer = self._resolve_placeholders(footer_html or "", variables_dict)

        resolved_body = self._apply_page_breaks(resolved_body)
        resolved_body = self._apply_table_support(resolved_body)
        resolved_body = self._apply_image_support(resolved_body)

        resolved_header = self._apply_table_support(resolved_header)
        resolved_header = self._apply_image_support(resolved_header)

        resolved_footer = self._apply_table_support(resolved_footer)
        resolved_footer = self._apply_image_support(resolved_footer)

        css = self._compose_styles(
            page_size=page_size,
            orientation=orientation,
            margin_top=margin_top,
            margin_bottom=margin_bottom,
            margin_left=margin_left,
            margin_right=margin_right,
            header_height=header_height,
            footer_height=footer_height,
            style_overrides=style_overrides or "",
        )

        header_section = (
            f'<header class="document-header">{resolved_header}</header>'
            if include_header and resolved_header
            else ""
        )
        footer_section = (
            f'<footer class="document-footer">{resolved_footer}</footer>'
            if include_footer and resolved_footer
            else ""
        )

        html_output = (
            "<!DOCTYPE html>"
            "<html lang=\"en\">"
            "<head>"
            "<meta charset=\"utf-8\"/>"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"/>"
            f"<title>{html.escape(template_name or 'Document')}</title>"
            f"<style>{css}</style>"
            "</head>"
            "<body>"
            "<div class=\"document-shell\">"
            f"{header_section}"
            f"<main class=\"document-content\">{resolved_body}</main>"
            f"{footer_section}"
            "</div>"
            "</body>"
            "</html>"
        )

        self._log(
            execution_log,
            stage="HTML_BUILD_COMPLETE",
            message="HTML build completed.",
            metadata={
                "html_length": len(html_output),
                "contains_page_break": "page-break" in resolved_body,
            },
        )

        return {
            "html": html_output,
            "body_html": resolved_body,
            "header_html": resolved_header,
            "footer_html": resolved_footer,
            "css": css,
            "page_size": page_size,
            "orientation": orientation,
            "execution_log": execution_log,
        }
