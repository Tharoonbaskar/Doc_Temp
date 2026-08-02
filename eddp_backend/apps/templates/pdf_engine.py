from __future__ import annotations

import copy
import html
import json
import re
from io import BytesIO
from typing import Any

from django.conf import settings
from django.utils import timezone

from apps.common.exceptions import ExternalServiceException, ValidationException


PLACEHOLDER_PATTERN = re.compile(
    r"<\s*([A-Za-z][A-Za-z0-9_]*)\s*>"
    r"|\{\{\s*([A-Za-z][A-Za-z0-9_]*)\s*\}\}"
    r"|\{\s*([A-Za-z][A-Za-z0-9_]*)\s*\}"
)

DYNAMIC_TABLE_TOKENS = {
    "ADDRESS_TABLE",
    "SIGNATURE_TABLE",
    "AMORTIZATION_TABLE",
    "PAYMENT_SCHEDULE",
    "CO_APPLICANT_TABLE",
    "CUSTOMER_TABLE",
}

SIGNATURE_TOKENS = {
    "SIGNATURE",
    "AUTHORIZED_SIGNATORY",
    "CO_APPLICANT_SIGNATURE",
    "SIGNATURE_TABLE",
}

IMAGE_TOKENS = {
    "CUSTOMER_PHOTO",
    "PROPERTY_IMAGE",
    "QR_CODE",
    "COMPANY_LOGO",
}

PAGE_DIMENSIONS_PX: dict[str, dict[str, int]] = {
    "A4": {"width": 794, "height": 1123},
    "A3": {"width": 1123, "height": 1587},
    "LETTER": {"width": 816, "height": 1056},
    "LEGAL": {"width": 816, "height": 1344},
}

PAGE_DIMENSIONS_MM: dict[str, dict[str, int]] = {
    "A4": {"width": 210, "height": 297},
    "A3": {"width": 297, "height": 420},
    "LETTER": {"width": 216, "height": 279},
    "LEGAL": {"width": 216, "height": 356},
}

ALLOWED_PAGE_SIZES = set(PAGE_DIMENSIONS_PX.keys())
ALLOWED_ORIENTATIONS = {"PORTRAIT", "LANDSCAPE"}


class EnterprisePDFEngine:
    """Render enterprise PDFs from approved ProseMirror JSON only."""

    def _normalize_token(self, raw: str) -> str:
        token = re.sub(r"[^A-Za-z0-9_]+", "_", str(raw or "").strip().upper())
        token = re.sub(r"_+", "_", token)
        return token.strip("_")

    def _normalize_page_size(self, value: str) -> str:
        candidate = str(value or "A4").strip().upper()
        return candidate if candidate in ALLOWED_PAGE_SIZES else "A4"

    def _normalize_orientation(self, value: str) -> str:
        candidate = str(value or "PORTRAIT").strip().upper()
        return candidate if candidate in ALLOWED_ORIENTATIONS else "PORTRAIT"

    def _to_float(self, value: Any, default: float, *, minimum: float = 0.0, maximum: float = 200.0) -> float:
        if value in (None, ""):
            return default
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, parsed))

    def _normalize_layout_options(self, template, options: dict[str, Any] | None) -> dict[str, Any]:
        opts = dict(options or {})
        page_size = self._normalize_page_size(str(opts.get("page_size") or template.page_size or "A4"))
        orientation = self._normalize_orientation(
            str(opts.get("orientation") or opts.get("page_orientation") or template.page_orientation or "PORTRAIT")
        )

        return {
            "page_size": page_size,
            "orientation": orientation,
            "margin_top_mm": self._to_float(opts.get("margin_top_mm"), 14.0),
            "margin_bottom_mm": self._to_float(opts.get("margin_bottom_mm"), 14.0),
            "margin_left_mm": self._to_float(opts.get("margin_left_mm"), 14.0),
            "margin_right_mm": self._to_float(opts.get("margin_right_mm"), 14.0),
            "header_height_mm": self._to_float(opts.get("header_height_mm"), 12.0),
            "footer_height_mm": self._to_float(opts.get("footer_height_mm"), 12.0),
            "resolution_dpi": int(self._to_float(opts.get("resolution_dpi"), 150.0, minimum=72.0, maximum=600.0)),
            "watermark": str(str(opts.get("watermark") or "")).strip(),
            "include_header_footer": bool(opts.get("include_header_footer", True)),
            "include_page_numbers": bool(opts.get("include_page_numbers", True)),
            "variable_resolution_mode": str(str(opts.get("variable_resolution_mode") or "RESOLVE_STRICT")).strip().upper(),
            "font_embedding": bool(opts.get("font_embedding", True)),
            "font_family": str(str(opts.get("font_family") or "Times New Roman")).strip() or "Times New Roman",
            "header_text": str(str(opts.get("header_text") or "")).strip(),
            "footer_text": str(str(opts.get("footer_text") or "")).strip(),
            "header_html": str(str(opts.get("header_html") or "")).strip(),
            "footer_html": str(str(opts.get("footer_html") or "")).strip(),
            "preview_unresolved": bool(opts.get("preview_unresolved", False)),
            "font_faces": opts.get("font_faces") if isinstance(opts.get("font_faces"), list) else [],
            "security": opts.get("security") if isinstance(opts.get("security"), dict) else {},
        }

    def _empty_doc(self) -> dict[str, Any]:
        return {"type": "doc", "content": [{"type": "paragraph"}]}

    def _coerce_prosemirror_doc(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict) and value.get("type") == "doc" and isinstance(value.get("content"), list):
            return value

        if isinstance(value, dict):
            nested = value.get("prosemirror_json")
            if isinstance(nested, dict):
                return self._coerce_prosemirror_doc(nested)

        if isinstance(value, str) and value.strip():
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return self._empty_doc()
            return self._coerce_prosemirror_doc(parsed)

        return self._empty_doc()

    def _flatten_variables(self, value: Any, prefix: str = "") -> dict[str, Any]:
        index: dict[str, Any] = {}

        if isinstance(value, dict):
            for raw_key, raw_val in value.items():
                key = self._normalize_token(raw_key)
                if not key:
                    continue
                full_key = key if not prefix else f"{prefix}_{key}"
                index[full_key] = raw_val
                index.update(self._flatten_variables(raw_val, full_key))
            return index

        if isinstance(value, list):
            for idx, item in enumerate(value):
                full_key = f"{prefix}_{idx}" if prefix else str(idx)
                index[full_key] = item
                index.update(self._flatten_variables(item, full_key))
            return index

        if prefix:
            index[prefix] = value
        return index

    def _lookup_variable(self, key: str, variables: dict[str, Any], variable_index: dict[str, Any]) -> Any:
        if key in variables:
            return variables[key]

        normalized = self._normalize_token(key)
        if not normalized:
            return None

        if normalized in variable_index:
            return variable_index[normalized]

        dotted = normalized.replace("_", ".")
        if dotted in variables:
            return variables[dotted]

        lowered = key.lower()
        for candidate_key, candidate_val in variables.items():
            if str(candidate_key).lower() == lowered:
                return candidate_val

        return None

    def _format_inr(self, numeric_value: float) -> str:
        absolute = abs(numeric_value)
        rounded = f"{absolute:.2f}" if not absolute.is_integer() else str(int(absolute))
        integer_part, dot, decimal_part = rounded.partition(".")

        if len(integer_part) > 3:
            last_three = integer_part[-3:]
            leading = integer_part[:-3]
            groups: list[str] = []
            while len(leading) > 2:
                groups.insert(0, leading[-2:])
                leading = leading[:-2]
            if leading:
                groups.insert(0, leading)
            integer_part = ",".join(groups + [last_three])

        prefix = "-" if numeric_value < 0 else ""
        if decimal_part and int(decimal_part) > 0:
            return f"{prefix}₹{integer_part}.{decimal_part}"
        return f"{prefix}₹{integer_part}"

    def _render_variable_value(self, token: str, value: Any) -> str:
        if value is None:
            return ""

        if isinstance(value, (int, float)) and any(
            hint in token for hint in ["AMOUNT", "BALANCE", "TOTAL", "VALUE", "LIMIT", "INTEREST"]
        ):
            return self._format_inr(float(value))

        if isinstance(value, bool):
            return "Yes" if value else "No"

        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=True)

        return str(value)

    def _build_dynamic_table_node(self, token: str, value: Any) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        headers: list[str] = []

        if isinstance(value, dict):
            value = [value]

        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    if not headers:
                        headers = [str(key) for key in item.keys()]
                    rows.append(item)
                else:
                    rows.append({"Value": item})

        if not headers and rows:
            first = rows[0]
            headers = [str(key) for key in first.keys()]

        if not headers:
            headers = ["Value"]
            rows = [{"Value": ""}]

        table_rows: list[dict[str, Any]] = [
            {
                "type": "tableRow",
                "content": [
                    {
                        "type": "tableHeader",
                        "content": [{"type": "paragraph", "content": [{"type": "text", "text": header}]}],
                    }
                    for header in headers
                ],
            }
        ]

        for row in rows:
            table_rows.append(
                {
                    "type": "tableRow",
                    "content": [
                        {
                            "type": "tableCell",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": self._render_variable_value(
                                                self._normalize_token(header), row.get(header)
                                            ),
                                        }
                                    ],
                                }
                            ],
                        }
                        for header in headers
                    ],
                }
            )

        return {"type": "table", "attrs": {"dynamic_source": token}, "content": table_rows}

    def _replace_text_placeholders(
        self,
        text: str,
        *,
        variables: dict[str, Any],
        variable_index: dict[str, Any],
        missing_tokens: set[str],
        resolution_mode: str,
    ) -> str:
        if not text:
            return text

        def repl(match: re.Match[str]) -> str:
            token = match.group(1) or match.group(2) or match.group(3) or ""
            normalized = self._normalize_token(token)
            resolved = self._lookup_variable(normalized, variables, variable_index)

            if resolved is None:
                if resolution_mode == "KEEP_UNRESOLVED":
                    return match.group(0)
                missing_tokens.add(normalized)
                return ""

            return self._render_variable_value(normalized, resolved)

        return PLACEHOLDER_PATTERN.sub(repl, text)

    def _resolve_variable_node(
        self,
        node: dict[str, Any],
        *,
        variables: dict[str, Any],
        variable_index: dict[str, Any],
        missing_tokens: set[str],
        resolution_mode: str,
    ) -> list[dict[str, Any]]:
        attrs = node.get("attrs") if isinstance(node.get("attrs"), dict) else {}
        raw_field = attrs.get("field") or attrs.get("binding") or attrs.get("variable") or attrs.get("variableKey")
        token = self._normalize_token(str(raw_field or ""))

        if not token:
            return []

        value = self._lookup_variable(token, variables, variable_index)
        node_type = str(node.get("type") or "")
        node_type_lower = node_type.lower()

        if value is None:
            if resolution_mode == "KEEP_UNRESOLVED":
                return [{"type": "text", "text": f"<{token}>"}]
            missing_tokens.add(token)
            return [{"type": "text", "text": ""}]

        if node_type_lower in {"dynamictablevariable", "dynamic_table_variable"} or token in DYNAMIC_TABLE_TOKENS:
            return [self._build_dynamic_table_node(token, value)]

        if node_type_lower in {"imageplaceholdervariable", "image_placeholder_variable"} or token in IMAGE_TOKENS:
            if isinstance(value, dict):
                src = str(str(value.get("src") or value.get("url") or "")).strip()
                alt = str(str(value.get("alt") or token.replace("_", " "))).strip()
            else:
                src = str(str(value)).strip()
                alt = token.replace("_", " ")
            if not src:
                return [{"type": "text", "text": ""}]
            return [
                {
                    "type": "image",
                    "attrs": {
                        "src": src,
                        "alt": alt,
                        "width": attrs.get("width"),
                        "height": attrs.get("height"),
                    },
                }
            ]

        if node_type_lower in {"signaturevariable", "signature_variable"} or token in SIGNATURE_TOKENS:
            if isinstance(value, dict):
                src = str(str(value.get("src") or value.get("url") or "")).strip()
                if src:
                    return [{"type": "image", "attrs": {"src": src, "alt": "Signature", "height": 56}}]
            text_value = self._render_variable_value(token, value).strip()
            if text_value:
                return [{"type": "text", "text": text_value}]
            return [{"type": "signatureBox", "attrs": {"label": "Authorized Signature"}}]

        return [{"type": "text", "text": self._render_variable_value(token, value)}]

    def _resolve_nodes(
        self,
        nodes: list[dict[str, Any]],
        *,
        variables: dict[str, Any],
        variable_index: dict[str, Any],
        missing_tokens: set[str],
        resolution_mode: str,
    ) -> list[dict[str, Any]]:
        resolved_nodes: list[dict[str, Any]] = []

        for raw_node in nodes:
            if not isinstance(raw_node, dict):
                continue

            node = copy.deepcopy(raw_node)
            node_type = str(node.get("type") or "")
            node_type_lower = node_type.lower()

            if node_type_lower == "text":
                node["text"] = self._replace_text_placeholders(
                    str(node.get("text") or ""),
                    variables=variables,
                    variable_index=variable_index,
                    missing_tokens=missing_tokens,
                    resolution_mode=resolution_mode,
                )
                resolved_nodes.append(node)
                continue

            if node_type_lower in {
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
                resolved_nodes.extend(
                    self._resolve_variable_node(
                        node,
                        variables=variables,
                        variable_index=variable_index,
                        missing_tokens=missing_tokens,
                        resolution_mode=resolution_mode,
                    )
                )
                continue

            content = node.get("content") if isinstance(node.get("content"), list) else None
            if content is not None:
                node["content"] = self._resolve_nodes(
                    content,
                    variables=variables,
                    variable_index=variable_index,
                    missing_tokens=missing_tokens,
                    resolution_mode=resolution_mode,
                )

            resolved_nodes.append(node)

        return resolved_nodes

    def _resolve_enterprise_variables(
        self,
        *,
        source_doc: dict[str, Any],
        variables: dict[str, Any],
        resolution_mode: str,
    ) -> tuple[dict[str, Any], list[str]]:
        variable_index = self._flatten_variables(variables)
        missing_tokens: set[str] = set()

        normalized_doc = self._coerce_prosemirror_doc(source_doc)
        doc_copy = copy.deepcopy(normalized_doc)
        content = doc_copy.get("content") if isinstance(doc_copy.get("content"), list) else []

        doc_copy["content"] = self._resolve_nodes(
            content,
            variables=variables,
            variable_index=variable_index,
            missing_tokens=missing_tokens,
            resolution_mode=resolution_mode,
        )

        if not doc_copy["content"]:
            doc_copy["content"] = [{"type": "paragraph"}]

        return doc_copy, sorted([token for token in missing_tokens if token])

    def _node_text_length(self, node: dict[str, Any]) -> int:
        node_type = str(node.get("type") or "")
        if node_type == "text":
            return len(str(node.get("text") or ""))
        content = node.get("content") if isinstance(node.get("content"), list) else []
        return sum(self._node_text_length(child) for child in content if isinstance(child, dict))

    def _flatten_text(self, node: dict[str, Any]) -> str:
        node_type = str(node.get("type") or "")
        if node_type == "text":
            return str(node.get("text") or "")
        content = node.get("content") if isinstance(node.get("content"), list) else []
        return " ".join(self._flatten_text(child) for child in content if isinstance(child, dict))

    def _estimate_table_height(self, node: dict[str, Any]) -> int:
        rows = [child for child in (node.get("content") or []) if isinstance(child, dict) and child.get("type") == "tableRow"]
        min_rows = max(len(rows), 1)
        return 36 + min_rows * 34

    def _estimate_block_height(self, node: dict[str, Any]) -> int:
        node_type = str(node.get("type") or "")
        if node_type == "heading":
            attrs = node.get("attrs") if isinstance(node.get("attrs"), dict) else {}
            try:
                level = int(attrs.get("level") or 1)
            except (TypeError, ValueError):
                level = 1
            line_height = 46 if level <= 1 else (38 if level == 2 else 32)
            text_length = max(self._node_text_length(node), 1)
            wrapped_lines = max(1, (text_length + 69) // 70)
            return line_height + (wrapped_lines - 1) * max(24, int(line_height * 0.6))

        if node_type == "paragraph":
            text_length = self._node_text_length(node)
            wrapped_lines = max(1, (max(text_length, 1) + 94) // 95)
            return 14 + wrapped_lines * 24

        if node_type in {"bulletList", "orderedList"}:
            content = node.get("content") if isinstance(node.get("content"), list) else []
            return 20 + max(len(content), 1) * 28

        if node_type == "table":
            return self._estimate_table_height(node)

        if node_type == "image":
            attrs = node.get("attrs") if isinstance(node.get("attrs"), dict) else {}
            try:
                return int(attrs.get("height") or 220)
            except (TypeError, ValueError):
                return 220

        if node_type in {"horizontalRule", "pageBreak"}:
            return 20

        text_length = self._node_text_length(node)
        if text_length > 0:
            return 20 + max(1, (text_length + 94) // 95) * 24
        return 28

    def _is_manual_page_break(self, node: dict[str, Any]) -> bool:
        if str(node.get("type") or "") != "pageBreak":
            return False
        attrs = node.get("attrs") if isinstance(node.get("attrs"), dict) else {}
        return attrs.get("auto") is not True

    def _is_heading(self, node: dict[str, Any]) -> bool:
        return str(node.get("type") or "") == "heading"

    def _is_likely_signature_block(self, node: dict[str, Any]) -> bool:
        if str(node.get("type") or "") != "paragraph":
            return False
        text = self._flatten_text(node).upper()
        return (
            "AUTHORISED SIGNATORY" in text
            or "AUTHORIZED SIGNATORY" in text
            or "SIGNATURE" in text
        )

    def _split_long_table(
        self,
        table_node: dict[str, Any],
        *,
        remaining_height: int,
        printable_height: int,
    ) -> list[dict[str, Any]] | None:
        if str(table_node.get("type") or "") != "table":
            return None

        rows = [child for child in (table_node.get("content") or []) if isinstance(child, dict) and child.get("type") == "tableRow"]
        if len(rows) <= 8:
            return None

        row_height = 34
        table_chrome = 24
        header_rows: list[dict[str, Any]] = []
        body_start = 0

        for idx, row in enumerate(rows):
            row_cells = row.get("content") if isinstance(row.get("content"), list) else []
            has_header = any(
                isinstance(cell, dict) and str(cell.get("type") or "") == "tableHeader"
                for cell in row_cells
            )
            if has_header:
                header_rows.append(row)
                body_start = idx + 1
            else:
                break

        body_rows = rows[body_start:]
        first_page_capacity = int(max(remaining_height - table_chrome, row_height) // row_height)
        next_page_capacity = int(max(printable_height - table_chrome, row_height) // row_height)

        if first_page_capacity <= len(header_rows) or next_page_capacity <= len(header_rows):
            return None

        if len(body_rows) <= first_page_capacity - len(header_rows):
            return None

        fragments: list[dict[str, Any]] = []
        body_index = 0
        rows_for_page = first_page_capacity - len(header_rows)

        while body_index < len(body_rows):
            chunk = body_rows[body_index : body_index + rows_for_page]
            fragment_rows = [copy.deepcopy(item) for item in (header_rows + chunk)]
            fragment = copy.deepcopy(table_node)
            fragment["content"] = fragment_rows
            fragments.append(fragment)

            body_index += len(chunk)
            rows_for_page = next_page_capacity - len(header_rows)

            if body_index < len(body_rows):
                fragments.append({"type": "pageBreak", "attrs": {"auto": True, "source": "table-split"}})

        return fragments

    def _clear_auto_page_breaks(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        cleaned: list[dict[str, Any]] = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if str(node.get("type") or "") == "pageBreak":
                attrs = node.get("attrs") if isinstance(node.get("attrs"), dict) else {}
                if attrs.get("auto") is True:
                    continue
            cleaned.append(node)
        return cleaned

    def _auto_paginate_doc(self, doc: dict[str, Any], *, page_size: str, orientation: str, margin_px: float) -> dict[str, Any]:
        base = PAGE_DIMENSIONS_PX.get(page_size, PAGE_DIMENSIONS_PX["A4"])
        page_height = base["width"] if orientation == "LANDSCAPE" else base["height"]
        printable_height = max(180, int(page_height - margin_px * 2 - 28))

        source_nodes = self._clear_auto_page_breaks(doc.get("content") if isinstance(doc.get("content"), list) else [])
        paginated: list[dict[str, Any]] = []
        remaining_height = printable_height

        for idx, node in enumerate(source_nodes):
            if self._is_manual_page_break(node):
                paginated.append(node)
                remaining_height = printable_height
                continue

            estimated_height = self._estimate_block_height(node)
            next_node = source_nodes[idx + 1] if idx + 1 < len(source_nodes) else None

            if self._is_heading(node) and next_node is not None:
                heading_cluster_height = estimated_height + self._estimate_block_height(next_node)
                if heading_cluster_height > remaining_height and paginated:
                    paginated.append({"type": "pageBreak", "attrs": {"auto": True, "source": "heading-keep-with-next"}})
                    remaining_height = printable_height

            node_type = str(node.get("type") or "")
            if (node_type == "table" or self._is_likely_signature_block(node)) and estimated_height > remaining_height and paginated:
                paginated.append({"type": "pageBreak", "attrs": {"auto": True, "source": "keep-together"}})
                remaining_height = printable_height

            if node_type == "table":
                table_split = self._split_long_table(node, remaining_height=remaining_height, printable_height=printable_height)
                if table_split:
                    for split_node in table_split:
                        split_type = str(split_node.get("type") or "")
                        if split_type == "pageBreak":
                            paginated.append(split_node)
                            remaining_height = printable_height
                            continue
                        paginated.append(split_node)
                        remaining_height -= self._estimate_block_height(split_node)
                    continue

            if estimated_height > remaining_height and paginated:
                paginated.append({"type": "pageBreak", "attrs": {"auto": True, "source": "overflow"}})
                remaining_height = printable_height

            paginated.append(node)
            remaining_height -= estimated_height

        next_doc = copy.deepcopy(doc)
        next_doc["content"] = paginated if paginated else [{"type": "paragraph"}]
        return next_doc

    def _page_dimensions_mm(self, page_size: str, orientation: str) -> tuple[int, int]:
        base = PAGE_DIMENSIONS_MM.get(page_size, PAGE_DIMENSIONS_MM["A4"])
        width = int(base["width"])
        height = int(base["height"])
        if orientation == "LANDSCAPE":
            return height, width
        return width, height

    def _render_mark(self, current_html: str, mark: dict[str, Any]) -> str:
        mark_type = str(mark.get("type") or "")
        attrs = mark.get("attrs") if isinstance(mark.get("attrs"), dict) else {}

        if mark_type == "bold":
            return f"<strong>{current_html}</strong>"
        if mark_type == "italic":
            return f"<em>{current_html}</em>"
        if mark_type == "underline":
            return f"<u>{current_html}</u>"
        if mark_type == "strike":
            return f"<s>{current_html}</s>"
        if mark_type == "code":
            return f"<code>{current_html}</code>"
        if mark_type == "link":
            href = html.escape(str(str(attrs.get("href") or "")).strip())
            if not href:
                return current_html
            target = html.escape(str(str(attrs.get("target") or "")))
            rel = html.escape(str(str(attrs.get("rel") or "noopener noreferrer")))
            target_attr = f' target="{target}"' if target else ""
            rel_attr = f' rel="{rel}"' if rel else ""
            return f"<a href=\"{href}\"{target_attr}{rel_attr}>{current_html}</a>"

        style_parts: list[str] = []
        if mark_type == "highlight":
            color = str(str(attrs.get("color") or "#fff59d")).strip()
            if color:
                style_parts.append(f"background-color:{html.escape(color)}")
        if mark_type == "textStyle":
            color = str(str(attrs.get("color") or "")).strip()
            if color:
                style_parts.append(f"color:{html.escape(color)}")
            bg = str(str(attrs.get("backgroundColor") or "")).strip()
            if bg:
                style_parts.append(f"background-color:{html.escape(bg)}")
            font_size = attrs.get("fontSize")
            if font_size not in (None, ""):
                style_parts.append(f"font-size:{html.escape(str(font_size))}")
        if mark_type == "color":
            color = str(str(attrs.get("color") or "")).strip()
            if color:
                style_parts.append(f"color:{html.escape(color)}")
        if mark_type == "fontFamily":
            family = str(str(attrs.get("fontFamily") or "")).strip()
            if family:
                style_parts.append(f"font-family:{html.escape(family)}")

        if style_parts:
            return f"<span style=\"{';'.join(style_parts)}\">{current_html}</span>"

        return current_html

    def _render_inline(self, node: dict[str, Any]) -> str:
        node_type = str(node.get("type") or "")

        if node_type == "text":
            text_html = html.escape(str(node.get("text") or ""))
            marks = node.get("marks") if isinstance(node.get("marks"), list) else []
            for mark in marks:
                if isinstance(mark, dict):
                    text_html = self._render_mark(text_html, mark)
            return text_html

        if node_type == "hardBreak":
            return "<br />"

        if node_type == "image":
            attrs = node.get("attrs") if isinstance(node.get("attrs"), dict) else {}
            src = str(str(attrs.get("src") or "")).strip()
            if not src:
                return ""
            alt = html.escape(str(str(attrs.get("alt") or "Image")))

            width = attrs.get("width")
            height = attrs.get("height")
            style_parts = ["max-width:100%", "height:auto"]
            if width not in (None, ""):
                style_parts.append(f"width:{html.escape(str(width))}px")
            if height not in (None, ""):
                style_parts.append(f"height:{html.escape(str(height))}px")

            return (
                f"<img class=\"eddp-image\" src=\"{html.escape(src)}\" alt=\"{alt}\" "
                f"style=\"{';'.join(style_parts)}\" />"
            )

        if node_type == "signatureBox":
            label = node.get("attrs", {}).get("label") if isinstance(node.get("attrs"), dict) else None
            return f"<div class=\"eddp-signature-box\">{html.escape(str(label or 'Signature'))}</div>"

        children = node.get("content") if isinstance(node.get("content"), list) else []
        return "".join(self._render_inline(child) for child in children if isinstance(child, dict))

    def _parse_style_map(self, style_text: Any) -> dict[str, str]:
        if not isinstance(style_text, str) or not style_text.strip():
            return {}

        parsed: dict[str, str] = {}
        for item in style_text.split(";"):
            segment = item.strip()
            if not segment or ":" not in segment:
                continue
            key, value = segment.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            if not key or not value:
                continue
            parsed[key] = value
        return parsed

    def _to_css_length(self, value: Any, default_unit: str = "pt") -> str:
        if value in (None, ""):
            return ""

        if isinstance(value, (int, float)):
            return f"{float(value):g}{default_unit}"

        text = str(value).strip()
        if not text:
            return ""

        if re.search(r"[a-z%]+$", text, flags=re.IGNORECASE):
            return text

        try:
            return f"{float(text):g}{default_unit}"
        except (TypeError, ValueError):
            return text

    def _docx_block_attrs(self, attrs: dict[str, Any]) -> dict[str, Any]:
        docx = attrs.get("docx")
        if isinstance(docx, dict):
            return docx
        return {}

    def _resolve_block_spacing(self, attrs: dict[str, Any]) -> dict[str, str]:
        docx = self._docx_block_attrs(attrs)

        line_height = attrs.get("lineHeight")
        if line_height in (None, ""):
            line_height = docx.get("lineSpacing")

        spacing_before = attrs.get("spacingBefore")
        if spacing_before in (None, ""):
            spacing_before = docx.get("spaceBefore")

        spacing_after = attrs.get("spacingAfter")
        if spacing_after in (None, ""):
            spacing_after = docx.get("spaceAfter")

        first_line_indent = attrs.get("firstLineIndent")
        if first_line_indent in (None, ""):
            first_line_indent = docx.get("firstLineIndent")

        left_indent = attrs.get("leftIndent")
        if left_indent in (None, ""):
            left_indent = docx.get("leftIndent")

        right_indent = attrs.get("rightIndent")
        if right_indent in (None, ""):
            right_indent = docx.get("rightIndent")

        resolved = {
            "line-height": self._to_css_length(line_height, "pt"),
            "margin-top": self._to_css_length(spacing_before, "pt"),
            "margin-bottom": self._to_css_length(spacing_after, "pt"),
            "text-indent": self._to_css_length(first_line_indent, "pt"),
            "margin-left": self._to_css_length(left_indent, "pt"),
            "margin-right": self._to_css_length(right_indent, "pt"),
        }

        return {key: value for key, value in resolved.items() if value}

    def _render_cell(self, cell: dict[str, Any]) -> str:
        cell_type = str(cell.get("type") or "")
        tag = "th" if cell_type == "tableHeader" else "td"
        attrs = cell.get("attrs") if isinstance(cell.get("attrs"), dict) else {}

        style_map = self._parse_style_map(attrs.get("style"))
        style_parts: list[str] = []

        text_align = str(str(style_map.get("text-align") or attrs.get("textAlign") or attrs.get("align") or "")).strip()
        if text_align:
            style_parts.append(f"text-align:{html.escape(text_align)}")

        vertical_align = str(str(style_map.get("vertical-align") or attrs.get("docxVerticalAlign") or "")).strip().lower()
        if vertical_align:
            normalized_vertical = {
                "center": "middle",
                "both": "middle",
            }.get(vertical_align, vertical_align)
            style_parts.append(f"vertical-align:{html.escape(normalized_vertical)}")

        bg_color = str(str(style_map.get("background-color") or attrs.get("backgroundColor") or "")).strip()
        if bg_color:
            style_parts.append(f"background-color:{html.escape(bg_color)}")

        for key in ("padding", "border", "width", "height", "min-height"):
            value = style_map.get(key)
            if value:
                style_parts.append(f"{key}:{html.escape(value)}")

        col_width = attrs.get("colwidth")
        if not style_map.get("width") and isinstance(col_width, list) and col_width:
            try:
                style_parts.append(f"width:{int(col_width[0])}px")
            except (TypeError, ValueError):
                pass

        colspan = attrs.get("colspan")
        rowspan = attrs.get("rowspan")
        colspan_attr = f' colspan="{int(colspan)}"' if isinstance(colspan, int) and colspan > 1 else ""
        rowspan_attr = f' rowspan="{int(rowspan)}"' if isinstance(rowspan, int) and rowspan > 1 else ""
        style_attr = f" style=\"{';'.join(style_parts)}\"" if style_parts else ""

        children = cell.get("content") if isinstance(cell.get("content"), list) else []
        content_html = "".join(self._render_block(child) for child in children if isinstance(child, dict))
        if not content_html:
            content_html = "&nbsp;"

        return f"<{tag}{colspan_attr}{rowspan_attr}{style_attr}>{content_html}</{tag}>"

    def _render_table_row(self, row: dict[str, Any]) -> str:
        attrs = row.get("attrs") if isinstance(row.get("attrs"), dict) else {}
        style_parts: list[str] = []

        row_height_pt = attrs.get("docxHeightPt")
        height_css = self._to_css_length(row_height_pt, "pt")
        if height_css:
            style_parts.append(f"height:{html.escape(height_css)}")

        style_attr = f" style=\"{';'.join(style_parts)}\"" if style_parts else ""
        cells_html = "".join(self._render_cell(cell) for cell in (row.get("content") or []) if isinstance(cell, dict))
        return f"<tr{style_attr}>{cells_html}</tr>"

    def _table_width_from_docx(self, attrs: dict[str, Any]) -> str:
        width_raw = str(str(attrs.get("docxTableWidth") or "")).strip()
        width_type = str(str(attrs.get("docxTableWidthType") or "")).strip().lower()

        if not width_raw:
            return ""

        try:
            width_num = float(width_raw)
        except (TypeError, ValueError):
            return ""

        if width_type == "pct":
            return f"{max(0.0, width_num / 50.0):g}%"

        if width_type in {"dxa", ""}:
            # dxa values are twips. 1 pt = 20 twips, 1 pt = 96/72 px.
            px = (width_num / 20.0) * (96.0 / 72.0)
            return f"{max(1.0, px):g}px"

        return ""

    def _render_table(self, table_node: dict[str, Any]) -> str:
        table_attrs = table_node.get("attrs") if isinstance(table_node.get("attrs"), dict) else {}
        table_style_map = self._parse_style_map(table_attrs.get("style"))

        rows = [row for row in (table_node.get("content") or []) if isinstance(row, dict) and row.get("type") == "tableRow"]
        if not rows:
            return "<table class=\"eddp-table\"></table>"

        header_rows: list[dict[str, Any]] = []
        body_rows: list[dict[str, Any]] = []
        header_phase = True

        for row in rows:
            cells = row.get("content") if isinstance(row.get("content"), list) else []
            has_header_cell = any(isinstance(cell, dict) and cell.get("type") == "tableHeader" for cell in cells)
            if header_phase and has_header_cell:
                header_rows.append(row)
            else:
                header_phase = False
                body_rows.append(row)

        if not header_rows:
            body_rows = rows

        head_html = ""
        if header_rows:
            head_html = "<thead>" + "".join(
                self._render_table_row(row)
                for row in header_rows
            ) + "</thead>"

        body_html = "<tbody>" + "".join(
            self._render_table_row(row)
            for row in body_rows
        ) + "</tbody>"

        table_style_parts: list[str] = []
        for key in ("width", "table-layout", "margin", "margin-top", "margin-bottom", "margin-left", "margin-right", "border-spacing", "border-collapse"):
            value = table_style_map.get(key)
            if value:
                table_style_parts.append(f"{key}:{html.escape(value)}")

        if not table_style_map.get("width"):
            docx_width = self._table_width_from_docx(table_attrs)
            if docx_width:
                table_style_parts.append(f"width:{html.escape(docx_width)}")

        if not table_style_map.get("margin"):
            table_align = str(str(table_attrs.get("textAlign") or "")).strip().lower()
            if table_align == "center":
                table_style_parts.append("margin-left:auto")
                table_style_parts.append("margin-right:auto")
            elif table_align == "right":
                table_style_parts.append("margin-left:auto")
                table_style_parts.append("margin-right:0")
            elif table_align == "left":
                table_style_parts.append("margin-left:0")
                table_style_parts.append("margin-right:auto")

        table_style_attr = f" style=\"{';'.join(table_style_parts)}\"" if table_style_parts else ""
        return f"<table class=\"eddp-table\"{table_style_attr}>{head_html}{body_html}</table>"

    def _render_block(self, node: dict[str, Any]) -> str:
        node_type = str(node.get("type") or "")
        attrs = node.get("attrs") if isinstance(node.get("attrs"), dict) else {}
        content = node.get("content") if isinstance(node.get("content"), list) else []

        if node_type == "paragraph":
            inline_html = "".join(self._render_inline(child) for child in content if isinstance(child, dict))
            style_parts: list[str] = []

            text_align = str(str(attrs.get("textAlign") or attrs.get("alignment") or "")).strip()
            if text_align:
                style_parts.append(f"text-align:{html.escape(text_align)}")

            resolved_spacing = self._resolve_block_spacing(attrs)
            style_parts.extend(f"{key}:{html.escape(value)}" for key, value in resolved_spacing.items())

            style_attr = f" style=\"{';'.join(style_parts)}\"" if style_parts else ""
            return f"<p{style_attr}>{inline_html or '&nbsp;'}</p>"

        if node_type == "heading":
            try:
                level = int(attrs.get("level") or 1)
            except (TypeError, ValueError):
                level = 1
            level = max(1, min(6, level))
            inline_html = "".join(self._render_inline(child) for child in content if isinstance(child, dict))
            
            # Apply styling attributes similar to paragraph rendering
            style_parts: list[str] = []
            
            text_align = str(str(attrs.get("textAlign") or attrs.get("alignment") or "")).strip()
            if text_align:
                style_parts.append(f"text-align:{html.escape(text_align)}")

            resolved_spacing = self._resolve_block_spacing(attrs)
            style_parts.extend(f"{key}:{html.escape(value)}" for key, value in resolved_spacing.items())
            
            style_attr = f" style=\"{';'.join(style_parts)}\"" if style_parts else ""
            return f"<h{level}{style_attr}>{inline_html or '&nbsp;'}</h{level}>"

        if node_type == "blockquote":
            children_html = "".join(self._render_block(child) for child in content if isinstance(child, dict))
            return f"<blockquote>{children_html}</blockquote>"

        if node_type in {"bulletList", "orderedList"}:
            tag = "ul" if node_type == "bulletList" else "ol"
            items_html = "".join(self._render_block(child) for child in content if isinstance(child, dict))
            return f"<{tag}>{items_html}</{tag}>"

        if node_type == "listItem":
            children_html = "".join(self._render_block(child) for child in content if isinstance(child, dict))
            return f"<li>{children_html}</li>"

        if node_type == "table":
            return self._render_table(node)

        if node_type in {"horizontalRule", "horizontal_rule"}:
            return "<hr />"

        if node_type == "image":
            return self._render_inline(node)

        if node_type == "codeBlock":
            inline_html = "".join(self._render_inline(child) for child in content if isinstance(child, dict))
            return f"<pre><code>{inline_html}</code></pre>"

        inline_fallback = "".join(self._render_inline(child) for child in content if isinstance(child, dict))
        if inline_fallback:
            return f"<p>{inline_fallback}</p>"

        return ""

    def _split_pages(self, doc: dict[str, Any]) -> list[list[dict[str, Any]]]:
        content = doc.get("content") if isinstance(doc.get("content"), list) else []
        pages: list[list[dict[str, Any]]] = [[]]

        for node in content:
            if not isinstance(node, dict):
                continue
            if str(node.get("type") or "") == "pageBreak":
                pages.append([])
                continue
            pages[-1].append(node)

        non_empty = [page for page in pages if page]
        return non_empty if non_empty else [[{"type": "paragraph"}]]

    def _resolve_html_template(
        self,
        template_html: str,
        *,
        variables: dict[str, Any],
        variable_index: dict[str, Any],
        missing_tokens: set[str],
        resolution_mode: str,
    ) -> str:
        if not template_html:
            return ""

        def repl(match: re.Match[str]) -> str:
            token = match.group(1) or match.group(2) or match.group(3) or ""
            normalized = self._normalize_token(token)
            value = self._lookup_variable(normalized, variables, variable_index)
            if value is None:
                if resolution_mode == "KEEP_UNRESOLVED":
                    return match.group(0)
                missing_tokens.add(normalized)
                return ""
            return html.escape(self._render_variable_value(normalized, value))

        return PLACEHOLDER_PATTERN.sub(repl, template_html)

    def _compose_css(
        self,
        *,
        options: dict[str, Any],
        page_width_mm: int,
        page_height_mm: int,
        has_header_footer: bool,
    ) -> str:
        margin_top = options["margin_top_mm"]
        margin_bottom = options["margin_bottom_mm"]
        margin_left = options["margin_left_mm"]
        margin_right = options["margin_right_mm"]
        header_height = options["header_height_mm"] if has_header_footer else 0.0
        footer_height = options["footer_height_mm"] if has_header_footer else 0.0

        font_family = options["font_family"]
        font_stack = f"'{font_family}', Calibri, Arial, 'Times New Roman', sans-serif"

        font_face_css = ""
        if options.get("font_embedding"):
            for face in options.get("font_faces") or []:
                if not isinstance(face, dict):
                    continue
                family = str(str(face.get("family") or "")).strip()
                src = str(str(face.get("src") or "")).strip()
                if not family or not src:
                    continue
                weight = str(str(face.get("weight") or "normal")).strip()
                style = str(str(face.get("style") or "normal")).strip()
                font_face_css += (
                    "@font-face {"
                    f"font-family:'{html.escape(family)}';"
                    f"src:url('{html.escape(src)}');"
                    f"font-weight:{html.escape(weight)};"
                    f"font-style:{html.escape(style)};"
                    "}"
                )

        return (
            "@page { margin: 0; }"
            "html, body { margin: 0; padding: 0; background: #fff; }"
            f"body {{ font-family: {font_stack}; font-size: 12px; color: #111; }}"
            ".eddp-document { width: 100%; }"
            ".eddp-page {"
            f"width: {page_width_mm}mm;"
            f"min-height: {page_height_mm}mm;"
            "position: relative;"
            "box-sizing: border-box;"
            f"padding: {margin_top + header_height}mm {margin_right}mm {margin_bottom + footer_height}mm {margin_left}mm;"
            "page-break-after: always;"
            "overflow: hidden;"
            "}"
            ".eddp-page:last-child { page-break-after: auto; }"
            ".eddp-header, .eddp-footer { position: absolute; left: 0; right: 0; box-sizing: border-box; }"
            f".eddp-header {{ top: {margin_top}mm; height: {header_height}mm; padding: 0 {margin_right}mm 0 {margin_left}mm; }}"
            f".eddp-footer {{ bottom: {margin_bottom}mm; height: {footer_height}mm; padding: 0 {margin_right}mm 0 {margin_left}mm; }}"
            ".eddp-content { width: 100%; }"
            ".eddp-page-number { position: absolute; right: 0; font-size: 10px; color: #4b5563; }"
            f".eddp-page-number {{ bottom: {max(margin_bottom - 4.0, 2.0)}mm; right: {margin_right}mm; }}"
            ".eddp-watermark {"
            "position: absolute;"
            "left: 50%;"
            "top: 50%;"
            "transform: translate(-50%, -50%) rotate(-30deg);"
            "font-size: 42px;"
            "color: rgba(128, 128, 128, 0.18);"
            "letter-spacing: 3px;"
            "pointer-events: none;"
            "white-space: nowrap;"
            "}"
            ".eddp-table { border-collapse: collapse; width: 100%; margin: 8px 0; table-layout: fixed; }"
            ".eddp-table thead { display: table-header-group; }"
            ".eddp-table tfoot { display: table-footer-group; }"
            ".eddp-table tr, .eddp-table td, .eddp-table th { break-inside: avoid; page-break-inside: avoid; }"
            ".eddp-table th, .eddp-table td { border: 1px solid #111827; padding: 6px; vertical-align: top; word-wrap: break-word; }"
            ".eddp-image { max-width: 100%; object-fit: contain; }"
            ".eddp-signature-box { border-top: 1px solid #111827; padding-top: 6px; min-height: 24px; display: inline-block; min-width: 180px; }"
            "p { margin: 0 0 8px 0; }"
            "h1,h2,h3,h4,h5,h6 { margin: 0 0 10px 0; }"
            "ul,ol { margin: 0 0 8px 20px; padding: 0; }"
            "blockquote { margin: 0 0 10px 0; padding-left: 10px; border-left: 3px solid #9ca3af; }"
            f"{font_face_css}"
        )

    def _build_html_document(
        self,
        *,
        pages: list[list[dict[str, Any]]],
        template,
        template_version,
        options: dict[str, Any],
        resolved_header_html: str,
        resolved_footer_html: str,
    ) -> str:
        page_width_mm, page_height_mm = self._page_dimensions_mm(options["page_size"], options["orientation"])
        total_pages = len(pages)
        include_header_footer = options["include_header_footer"] and (resolved_header_html or resolved_footer_html)

        css = self._compose_css(
            options=options,
            page_width_mm=page_width_mm,
            page_height_mm=page_height_mm,
            has_header_footer=bool(include_header_footer),
        )

        sections: list[str] = []
        watermark = options.get("watermark") or ""

        for page_index, page_nodes in enumerate(pages, start=1):
            body_html = "".join(self._render_block(node) for node in page_nodes)
            header_html = ""
            footer_html = ""

            if include_header_footer:
                header_content = resolved_header_html or html.escape(options.get("header_text") or "")
                footer_content = resolved_footer_html or html.escape(options.get("footer_text") or "")
                header_html = f"<header class=\"eddp-header\">{header_content}</header>"
                footer_html = f"<footer class=\"eddp-footer\">{footer_content}</footer>"

            watermark_html = (
                f"<div class=\"eddp-watermark\">{html.escape(str(watermark))}</div>"
                if watermark
                else ""
            )

            page_number_html = ""
            if options.get("include_page_numbers"):
                page_number_html = (
                    f"<div class=\"eddp-page-number\">Page {page_index} of {total_pages}</div>"
                )

            sections.append(
                "<section class=\"eddp-page\">"
                f"{watermark_html}"
                f"{header_html}"
                f"<main class=\"eddp-content\">{body_html or '<p>&nbsp;</p>'}</main>"
                f"{footer_html}"
                f"{page_number_html}"
                "</section>"
            )

        return (
            "<!DOCTYPE html>"
            "<html lang=\"en\">"
            "<head>"
            "<meta charset=\"utf-8\" />"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />"
            f"<title>{html.escape(str(template.name))}</title>"
            f"<style>{css}</style>"
            "</head>"
            "<body>"
            "<div class=\"eddp-document\">"
            + "".join(sections)
            + "</div></body></html>"
        )

    def _build_metadata(self, *, template, template_version, generated_by: str, metadata_overrides: dict[str, Any]) -> dict[str, str]:
        created_on = timezone.now().isoformat()
        merged = {
            "TemplateName": str(template.name),
            "TemplateCode": str(template.code),
            "Version": str(template_version.version_name),
            "ApprovalVersion": str(template_version.version_name),
            "GeneratedBy": str(generated_by or "System"),
            "GeneratedOn": created_on,
            "DocumentID": str(template.id),
            "Organization": str(metadata_overrides.get("Organization") or metadata_overrides.get("organization") or ""),
            "Classification": str(metadata_overrides.get("Classification") or metadata_overrides.get("classification") or "CONFIDENTIAL"),
        }

        for key, value in (metadata_overrides or {}).items():
            if value in (None, ""):
                continue
            merged[str(key)] = str(value)

        return merged

    def _apply_pdf_post_processing(
        self,
        *,
        pdf_bytes: bytes,
        metadata: dict[str, str],
        security: dict[str, Any],
    ) -> tuple[bytes, list[str]]:
        warnings: list[str] = []
        needs_post_process = bool(metadata) or bool(security.get("password"))
        if not needs_post_process:
            return pdf_bytes, warnings

        try:
            from pypdf import PdfReader, PdfWriter
        except Exception:
            warnings.append("pypdf is not installed; metadata/password options were skipped.")
            return pdf_bytes, warnings

        try:
            reader = PdfReader(BytesIO(pdf_bytes))
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)

            if metadata:
                writer.add_metadata({f"/{key}": value for key, value in metadata.items() if value})

            password = str(str(security.get("password") or "")).strip()
            if password:
                owner_password = str(str(security.get("owner_password") or password)).strip()
                restrict_printing = bool(security.get("restrict_printing"))
                restrict_copy = bool(security.get("restrict_copy"))
                permissions_flag = None

                if restrict_printing or restrict_copy:
                    warnings.append(
                        "PDF print/copy restrictions depend on the viewer; password protection is applied."
                    )

                try:
                    writer.encrypt(
                        user_password=password,
                        owner_password=owner_password,
                        permissions_flag=permissions_flag,
                    )
                except TypeError:
                    writer.encrypt(password, owner_password)

            output = BytesIO()
            writer.write(output)
            return output.getvalue(), warnings
        except Exception as exc:
            warnings.append(f"PDF post-processing skipped: {exc}")
            return pdf_bytes, warnings

    def _render_pdf_bytes(self, html_document: str) -> bytes:
        try:
            from xhtml2pdf import pisa
        except ImportError as exc:
            raise ExternalServiceException(
                detail=(
                    "xhtml2pdf is not installed. "
                    "Install it with: pip install xhtml2pdf"
                )
            ) from exc

        try:
            output = BytesIO()
            
            # Configure xhtml2pdf options for better rendering
            # Convert HTML to PDF with proper encoding.
            pisa_status = pisa.CreatePDF(
                src=html_document,
                dest=output,
                encoding='UTF-8',
                xhtml=False  # Don't require strict XHTML
            )
            
            if pisa_status.err:
                raise ExternalServiceException(
                    detail=f"PDF rendering failed with {pisa_status.err} errors."
                )
            
            return output.getvalue()
        except Exception as exc:
            raise ExternalServiceException(
                detail=f"PDF rendering failed: {exc}"
            ) from exc

    def generate_document_pdf(
        self,
        *,
        template,
        template_version,
        variables: dict[str, Any] | None,
        options: dict[str, Any] | None,
        metadata_overrides: dict[str, Any] | None,
        generated_by: str,
    ) -> dict[str, Any]:
        normalized_options = self._normalize_layout_options(template, options)
        resolution_mode = normalized_options.get("variable_resolution_mode", "RESOLVE_STRICT")
        if resolution_mode not in {"RESOLVE_STRICT", "KEEP_UNRESOLVED"}:
            raise ValidationException(detail="variable_resolution_mode must be RESOLVE_STRICT or KEEP_UNRESOLVED.")

        source_doc = self._coerce_prosemirror_doc(template_version.template_json)
        resolved_doc, missing_tokens = self._resolve_enterprise_variables(
            source_doc=source_doc,
            variables=variables or {},
            resolution_mode=resolution_mode,
        )

        template_json = template_version.template_json if isinstance(template_version.template_json, dict) else {}
        variable_index = self._flatten_variables(variables or {})
        header_template = normalized_options.get("header_html") or str(template_json.get("header_html") or "")
        footer_template = normalized_options.get("footer_html") or str(template_json.get("footer_html") or "")

        header_missing: set[str] = set()
        resolved_header = self._resolve_html_template(
            header_template,
            variables=variables or {},
            variable_index=variable_index,
            missing_tokens=header_missing,
            resolution_mode=resolution_mode,
        )
        resolved_footer = self._resolve_html_template(
            footer_template,
            variables=variables or {},
            variable_index=variable_index,
            missing_tokens=header_missing,
            resolution_mode=resolution_mode,
        )

        combined_missing = sorted(set(missing_tokens).union(header_missing))

        if combined_missing and not normalized_options.get("preview_unresolved") and resolution_mode != "KEEP_UNRESOLVED":
            raise ValidationException(
                detail=(
                    "Missing runtime variable values for: "
                    + ", ".join(combined_missing)
                    + ". Provide values or switch preview mode to KEEP_UNRESOLVED."
                )
            )

        avg_margin_mm = (
            normalized_options["margin_top_mm"]
            + normalized_options["margin_bottom_mm"]
            + normalized_options["margin_left_mm"]
            + normalized_options["margin_right_mm"]
        ) / 4.0
        margin_px = avg_margin_mm * (96.0 / 25.4)

        paginated_doc = self._auto_paginate_doc(
            resolved_doc,
            page_size=normalized_options["page_size"],
            orientation=normalized_options["orientation"],
            margin_px=margin_px,
        )
        pages = self._split_pages(paginated_doc)

        html_document = self._build_html_document(
            pages=pages,
            template=template,
            template_version=template_version,
            options=normalized_options,
            resolved_header_html=resolved_header,
            resolved_footer_html=resolved_footer,
        )

        metadata = self._build_metadata(
            template=template,
            template_version=template_version,
            generated_by=generated_by,
            metadata_overrides=metadata_overrides or {},
        )

        pdf_bytes = self._render_pdf_bytes(html_document)
        secured_pdf, warnings = self._apply_pdf_post_processing(
            pdf_bytes=pdf_bytes,
            metadata=metadata,
            security=normalized_options.get("security") or {},
        )

        return {
            "pdf_bytes": secured_pdf,
            "page_count": len(pages),
            "missing_variables": combined_missing,
            "metadata": metadata,
            "warnings": warnings,
            "options": normalized_options,
            "html": html_document,
        }
