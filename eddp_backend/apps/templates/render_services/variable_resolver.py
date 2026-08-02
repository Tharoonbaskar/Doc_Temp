from __future__ import annotations

import re
from typing import Any

from ..models import TemplateVersion
from ..pdf_engine import EnterprisePDFEngine


_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([A-Za-z0-9_.-]+)\s*\}\}|<([A-Za-z0-9_.-]+)>|#\{\s*([A-Za-z0-9_.-]+)\s*\}")


class VariableResolver:
    def __init__(self, pdf_engine: EnterprisePDFEngine | None = None) -> None:
        self.pdf_engine = pdf_engine or EnterprisePDFEngine()

    def _normalize_token(self, token: str) -> str:
        return self.pdf_engine._normalize_token(token)

    def _extract_text_tokens(self, text: str) -> set[str]:
        tokens: set[str] = set()
        if not text:
            return tokens

        for match in _PLACEHOLDER_PATTERN.finditer(text):
            raw = match.group(1) or match.group(2) or match.group(3) or ""
            normalized = self._normalize_token(raw)
            if normalized:
                tokens.add(normalized)
        return tokens

    def _extract_from_node(self, node: Any) -> set[str]:
        tokens: set[str] = set()
        if not isinstance(node, dict):
            return tokens

        node_type = str(node.get("type") or "").lower()
        attrs = node.get("attrs") if isinstance(node.get("attrs"), dict) else {}

        if node_type == "text":
            tokens.update(self._extract_text_tokens(str(node.get("text") or "")))

        if node_type in {
            "variablechip",
            "variable_chip",
            "variable",
            "dynamictablevariable",
            "dynamic_table_variable",
            "imageplaceholdervariable",
            "image_placeholder_variable",
            "signaturevariable",
            "signature_variable",
        }:
            raw_field = attrs.get("field") or attrs.get("binding") or attrs.get("variable") or attrs.get("variableKey")
            normalized = self._normalize_token(str(raw_field or ""))
            if normalized:
                tokens.add(normalized)

        for child in node.get("content") or []:
            tokens.update(self._extract_from_node(child))

        return tokens

    def extract_required_variables(self, template_version: TemplateVersion) -> set[str]:
        source = template_version.template_json if isinstance(template_version.template_json, dict) else {}
        doc = self.pdf_engine._coerce_prosemirror_doc(source)

        tokens: set[str] = set()
        for node in doc.get("content") or []:
            tokens.update(self._extract_from_node(node))

        header = str(source.get("header_html") or "")
        footer = str(source.get("footer_html") or "")
        tokens.update(self._extract_text_tokens(header))
        tokens.update(self._extract_text_tokens(footer))

        return {item for item in tokens if item}

    def find_missing_variables(self, template_version: TemplateVersion, payload: dict[str, Any]) -> list[str]:
        required = self.extract_required_variables(template_version)
        if not required:
            return []

        index = self.pdf_engine._flatten_variables(payload or {})
        missing = sorted([token for token in required if token not in index])
        return missing
