from __future__ import annotations

import html
import json
import re
from decimal import Decimal
from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone

from apps.common.exceptions import ResourceNotFoundException, ValidationException
from apps.common.validators import validate_json
from apps.templates.models import TemplateComponent, TemplateStyle, TemplateVersion

from ..repositories import RuntimeEngineRepository
from .expression import evaluate_safe_expression

_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_.\[\]]+)\s*\}\}")
_TBODY_REPEAT_PATTERN = re.compile(
    r"<tbody([^>]*)data-repeat\s*=\s*[\"']([^\"']+)[\"']([^>]*)>(.*?)</tbody>",
    flags=re.IGNORECASE | re.DOTALL,
)


class TemplateRenderingService:
    def __init__(self, repository: RuntimeEngineRepository | None = None) -> None:
        self.repository = repository or RuntimeEngineRepository()

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
    def _ensure_list(value: Any, field_name: str) -> list[Any]:
        if value is None:
            return []
        try:
            parsed = validate_json(value)
        except DjangoValidationError as exc:
            raise ValidationException(detail=str(exc)) from exc
        if not isinstance(parsed, list):
            raise ValidationException(detail=f"{field_name} must be a JSON array.")
        return parsed

    @staticmethod
    def _coerce_template_json(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str) and value.strip():
            try:
                parsed = json.loads(value)
            except Exception:
                return {}
            if isinstance(parsed, dict):
                return parsed
            return {}
        return {}

    @staticmethod
    def _coerce_prosemirror_doc(value: Any) -> dict[str, Any]:
        if isinstance(value, dict) and value.get("type") == "doc":
            return value

        if isinstance(value, dict):
            candidate = value.get("prosemirror_json")
            if isinstance(candidate, dict) and candidate.get("type") == "doc":
                return candidate

        if isinstance(value, str) and value.strip():
            try:
                parsed = json.loads(value)
            except Exception:
                return {"type": "doc", "content": [{"type": "paragraph"}]}
            return TemplateRenderingService._coerce_prosemirror_doc(parsed)

        return {"type": "doc", "content": [{"type": "paragraph"}]}

    def _render_prosemirror_marks(self, text_value: str, marks: Any) -> str:
        rendered = html.escape(text_value or "")
        if not isinstance(marks, list):
            return rendered

        for mark in marks:
            if not isinstance(mark, dict):
                continue
            mark_type = str(mark.get("type") or "").lower()
            attrs = mark.get("attrs") if isinstance(mark.get("attrs"), dict) else {}

            if mark_type == "bold":
                rendered = f"<strong>{rendered}</strong>"
            elif mark_type == "italic":
                rendered = f"<em>{rendered}</em>"
            elif mark_type == "underline":
                rendered = f"<u>{rendered}</u>"
            elif mark_type == "strike":
                rendered = f"<s>{rendered}</s>"
            elif mark_type == "code":
                rendered = f"<code>{rendered}</code>"
            elif mark_type == "link":
                href = html.escape(str(attrs.get("href") or "").strip())
                target = html.escape(str(attrs.get("target") or ""))
                rel = html.escape(str(attrs.get("rel") or ""))
                attr_parts = [f'href="{href}"'] if href else []
                if target:
                    attr_parts.append(f'target="{target}"')
                if rel:
                    attr_parts.append(f'rel="{rel}"')
                rendered = f"<a {' '.join(attr_parts)}>{rendered}</a>" if attr_parts else rendered

        return rendered

    def _render_prosemirror_inline(self, node: Any, context: dict[str, Any]) -> str:
        if not isinstance(node, dict):
            return ""

        node_type = str(node.get("type") or "").lower()
        attrs = node.get("attrs") if isinstance(node.get("attrs"), dict) else {}

        if node_type == "text":
            text_value = str(node.get("text") or "")
            marks = node.get("marks")
            return self._render_prosemirror_marks(text_value, marks)

        if node_type == "hardbreak":
            return "<br />"

        if node_type in {"variablechip", "variable_chip", "variable"}:
            field = str(attrs.get("field") or attrs.get("binding") or "").strip()
            label = str(attrs.get("label") or field).strip()
            value = self._get_by_path(context, field) if field else None
            if value is None:
                fallback = label or field
                return html.escape(fallback)
            rendered = value if isinstance(value, str) else json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            return html.escape(rendered)

        if node_type == "image":
            src = str(attrs.get("src") or "").strip()
            alt = str(attrs.get("alt") or "Image")
            if not src:
                return ""
            return f'<img class="template-image" src="{html.escape(src)}" alt="{html.escape(alt)}" />'

        children = node.get("content") if isinstance(node.get("content"), list) else []
        return "".join(self._render_prosemirror_inline(child, context) for child in children)

    def _render_prosemirror_block(self, node: Any, context: dict[str, Any]) -> str:
        if not isinstance(node, dict):
            return ""

        node_type = str(node.get("type") or "").lower()
        attrs = node.get("attrs") if isinstance(node.get("attrs"), dict) else {}
        children = node.get("content") if isinstance(node.get("content"), list) else []

        if node_type == "paragraph":
            inline = "".join(self._render_prosemirror_inline(child, context) for child in children)
            return f"<p>{inline}</p>"

        if node_type == "heading":
            level = attrs.get("level")
            try:
                heading_level = int(level)
            except Exception:
                heading_level = 1
            heading_level = max(1, min(6, heading_level))
            inline = "".join(self._render_prosemirror_inline(child, context) for child in children)
            return f"<h{heading_level}>{inline}</h{heading_level}>"

        if node_type in {"bulletlist", "orderedlist"}:
            tag = "ul" if node_type == "bulletlist" else "ol"
            items_html = "".join(self._render_prosemirror_block(child, context) for child in children)
            return f"<{tag}>{items_html}</{tag}>"

        if node_type == "listitem":
            item_html = "".join(self._render_prosemirror_block(child, context) for child in children)
            return f"<li>{item_html}</li>"

        if node_type == "blockquote":
            block_html = "".join(self._render_prosemirror_block(child, context) for child in children)
            return f"<blockquote>{block_html}</blockquote>"

        if node_type == "codeblock":
            raw_text = "".join(self._render_prosemirror_inline(child, context) for child in children)
            return f"<pre><code>{raw_text}</code></pre>"

        if node_type in {"horizontalrule", "horizontal_rule"}:
            return "<hr />"

        if node_type == "table":
            table_rows = "".join(self._render_prosemirror_block(child, context) for child in children)
            return f"<table class=\"template-table\">{table_rows}</table>"

        if node_type == "tablerow":
            cells = "".join(self._render_prosemirror_block(child, context) for child in children)
            return f"<tr>{cells}</tr>"

        if node_type in {"tablecell", "tableheader"}:
            tag = "th" if node_type == "tableheader" else "td"
            cell_html = "".join(self._render_prosemirror_block(child, context) for child in children)
            return f"<{tag}>{cell_html}</{tag}>"

        # Fallback: render unknown block as paragraph with inline content.
        inline_fallback = "".join(self._render_prosemirror_inline(child, context) for child in children)
        if inline_fallback:
            return f"<p>{inline_fallback}</p>"

        return ""

    def _prosemirror_doc_to_html(self, doc: Any, context: dict[str, Any]) -> str:
        pm_doc = self._coerce_prosemirror_doc(doc)
        content = pm_doc.get("content") if isinstance(pm_doc.get("content"), list) else []
        if not content:
            return "<p></p>"

        rendered_blocks = [self._render_prosemirror_block(node, context) for node in content]
        html_blocks = [block for block in rendered_blocks if block]
        return "".join(html_blocks) if html_blocks else "<p></p>"

    @staticmethod
    def _extract_data_field(fragment: str) -> str:
        match = re.search(r'data-field\s*=\s*["\']([^"\']+)["\']', fragment, flags=re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _replace_variable_chip_spans(self, template: str, context: dict[str, Any]) -> str:
        if not isinstance(template, str) or 'data-field' not in template:
            return template

        span_pattern = re.compile(r'<span[^>]*data-field\s*=\s*["\'][^"\']+["\'][^>]*>.*?</span>', flags=re.IGNORECASE | re.DOTALL)

        def _replace(match: re.Match[str]) -> str:
            raw_tag = match.group(0)
            field = self._extract_data_field(raw_tag)
            if not field:
                return ""
            value = self._get_by_path(context, field)
            if value is None:
                return ""
            rendered = value if isinstance(value, str) else json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            return html.escape(rendered)

        return span_pattern.sub(_replace, template)

    @staticmethod
    def _remove_data_repeat_attr(attrs: str) -> str:
        if not attrs:
            return ""
        return re.sub(r'\sdata-repeat\s*=\s*["\'][^"\']+["\']', '', attrs, flags=re.IGNORECASE)

    def _expand_repeat_tbody(self, template: str, context: dict[str, Any]) -> str:
        if not isinstance(template, str) or 'data-repeat' not in template:
            return template

        def _replace(match: re.Match[str]) -> str:
            attrs_left = match.group(1) or ""
            repeat_path = (match.group(2) or "").strip()
            attrs_right = match.group(3) or ""
            row_template = match.group(4) or ""

            items = self._get_by_path(context, repeat_path)
            if not isinstance(items, list):
                items = []

            rendered_rows: list[str] = []
            for index, item in enumerate(items):
                local_context = dict(context)
                local_context['index'] = index
                local_context['item'] = item
                if isinstance(item, dict):
                    local_context.update(item)
                rendered_rows.append(self._resolve_placeholders(row_template, local_context, escape_values=False))

            attrs = self._remove_data_repeat_attr(f"{attrs_left}{attrs_right}")
            return f"<tbody{attrs}>{''.join(rendered_rows)}</tbody>"

        return _TBODY_REPEAT_PATTERN.sub(_replace, template)

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

    def _resolve_placeholders(
        self,
        template: str,
        context: dict[str, Any],
        *,
        escape_values: bool = True,
    ) -> str:
        if not isinstance(template, str) or "{{" not in template:
            return template

        def replace(match: re.Match[str]) -> str:
            reference = match.group(1)
            value = self._get_by_path(context, reference)
            if value is None:
                return ""
            rendered = value if isinstance(value, str) else json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            return html.escape(rendered) if escape_values else rendered

        return _PLACEHOLDER_PATTERN.sub(replace, template)

    def _build_expression_context(
        self,
        variables: dict[str, Any],
        options: dict[str, Any],
    ) -> dict[str, Any]:
        context = {
            "variables": variables,
            "options": options,
        }
        context.update(variables)
        return context

    def _evaluate_condition(
        self,
        expression: str,
        *,
        variables: dict[str, Any],
        options: dict[str, Any],
    ) -> bool:
        if not expression:
            return True
        context = self._build_expression_context(variables, options)
        result = evaluate_safe_expression(expression, context)
        return bool(result)

    def _resolve_template_version(
        self,
        *,
        template_code: str,
        template_version_code: str,
        template_version_id: Any,
    ) -> TemplateVersion:
        template_version: TemplateVersion | None = None

        if template_version_id:
            template_version = self.repository.get_template_version_by_id(template_version_id)
        elif template_version_code:
            template_version = self.repository.get_template_version_by_code(template_version_code)
        elif template_code:
            template = self.repository.get_template_by_code(template_code)
            if template is None:
                raise ResourceNotFoundException(detail=f"Template '{template_code}' not found.")
            template_version = self.repository.get_active_template_version(template)

        if template_version is None:
            raise ResourceNotFoundException(detail="Template version could not be resolved.")

        return template_version

    @staticmethod
    def _decimal_to_css(value: Decimal | float | int | str) -> str:
        try:
            numeric = Decimal(str(value))
        except Exception:
            numeric = Decimal("0")
        return f"{numeric}mm"

    def _build_style_css(self, style: TemplateStyle | None) -> str:
        if style is None:
            return (
                "body { font-family: Arial, sans-serif; font-size: 12px; margin: 0; }"
                ".template-container { padding: 12px; }"
            )

        style_json = style.style_json if isinstance(style.style_json, dict) else {}
        custom_css = str(style_json.get("css") or style_json.get("custom_css") or "")

        return (
            "@page {"
            f" size: {style.page_size} {style.orientation.lower()};"
            f" margin-top: {self._decimal_to_css(style.margin_top)};"
            f" margin-bottom: {self._decimal_to_css(style.margin_bottom)};"
            f" margin-left: {self._decimal_to_css(style.margin_left)};"
            f" margin-right: {self._decimal_to_css(style.margin_right)};"
            " }"
            "body {"
            f" font-family: {html.escape(style.default_font)};"
            f" font-size: {int(style.default_font_size)}px;"
            " margin: 0;"
            "}"
            ".template-header { width: 100%; margin-bottom: 12px; }"
            ".template-footer { width: 100%; margin-top: 12px; }"
            ".template-content { width: 100%; }"
            "table.template-table { border-collapse: collapse; width: 100%; }"
            "table.template-table th, table.template-table td { border: 1px solid #444; padding: 6px; text-align: left; }"
            "img.template-image { max-width: 100%; height: auto; }"
            ".qr-placeholder, .barcode-placeholder { border: 1px dashed #777; padding: 8px; text-align: center; }"
            f"{custom_css}"
        )

    def _render_table(self, component_json: dict[str, Any], context: dict[str, Any]) -> str:
        headers = component_json.get("headers")
        rows = component_json.get("rows")

        rows_path = str(component_json.get("rows_path") or component_json.get("items_path") or "").strip()
        if rows is None and rows_path:
            rows = self._get_by_path(context, rows_path)

        if rows is None:
            rows = []

        if not isinstance(rows, list):
            raise ValidationException(detail="Table rows must be a list.")

        normalized_rows: list[dict[str, Any]] = []
        for item in rows:
            if isinstance(item, dict):
                normalized_rows.append(item)
            else:
                normalized_rows.append({"value": item})

        if headers is None:
            if normalized_rows:
                headers = list(normalized_rows[0].keys())
            else:
                headers = []

        if not isinstance(headers, list):
            raise ValidationException(detail="Table headers must be a list.")

        header_html = "".join(
            f"<th>{html.escape(str(header))}</th>" for header in headers
        )

        row_html_parts: list[str] = []
        for row in normalized_rows:
            cells = []
            for header in headers:
                value = row.get(header)
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                cells.append(f"<td>{html.escape('' if value is None else str(value))}</td>")
            row_html_parts.append(f"<tr>{''.join(cells)}</tr>")

        caption = str(component_json.get("caption") or "").strip()
        caption_html = f"<caption>{html.escape(caption)}</caption>" if caption else ""

        return (
            "<table class=\"template-table\">"
            f"{caption_html}"
            f"<thead><tr>{header_html}</tr></thead>"
            f"<tbody>{''.join(row_html_parts)}</tbody>"
            "</table>"
        )

    def _render_image(self, component_json: dict[str, Any], context: dict[str, Any]) -> str:
        source = str(component_json.get("src") or component_json.get("source") or "").strip()
        source_path = str(component_json.get("source_path") or "").strip()
        if not source and source_path:
            source_value = self._get_by_path(context, source_path)
            source = "" if source_value is None else str(source_value)
        if not source:
            return ""

        alt = str(component_json.get("alt") or "Image")
        width = str(component_json.get("width") or "").strip()
        height = str(component_json.get("height") or "").strip()

        size_attributes = ""
        if width:
            size_attributes += f" width=\"{html.escape(width)}\""
        if height:
            size_attributes += f" height=\"{html.escape(height)}\""

        return (
            f"<img class=\"template-image\" src=\"{html.escape(source)}\""
            f" alt=\"{html.escape(alt)}\"{size_attributes} />"
        )

    def _render_qr_or_barcode(
        self,
        *,
        component_json: dict[str, Any],
        context: dict[str, Any],
        mode: str,
    ) -> str:
        value = component_json.get("value")
        if value is None:
            value_path = str(component_json.get("value_path") or "").strip()
            if value_path:
                value = self._get_by_path(context, value_path)

        rendered_value = "" if value is None else str(value)
        css_class = "qr-placeholder" if mode == "qr" else "barcode-placeholder"
        label = "QR" if mode == "qr" else "BARCODE"

        return (
            f"<div class=\"{css_class}\" data-mode=\"{label}\" data-value=\"{html.escape(rendered_value)}\">"
            f"[{label}: {html.escape(rendered_value)}]"
            "</div>"
        )

    def _render_dynamic_section(
        self,
        section: dict[str, Any],
        *,
        variables: dict[str, Any],
        options: dict[str, Any],
    ) -> str:
        condition = str(section.get("condition") or "").strip()
        if condition and not self._evaluate_condition(condition, variables=variables, options=options):
            return ""

        items = section.get("items")
        items_path = str(section.get("items_path") or section.get("source_path") or "").strip()
        if items is None and items_path:
            items = self._get_by_path(variables, items_path)
        if items is None:
            items = []
        if not isinstance(items, list):
            raise ValidationException(detail="Dynamic section items must be a list.")

        item_name = str(section.get("item_name") or "item")
        row_template = str(section.get("row_template") or section.get("template") or "").strip()
        wrapper_tag = str(section.get("wrapper_tag") or "div").strip().lower()
        wrapper_class = str(section.get("class") or "dynamic-section").strip()

        row_fragments: list[str] = []
        for index, item in enumerate(items):
            local_context = dict(variables)
            local_context[item_name] = item
            local_context["index"] = index
            if isinstance(item, dict):
                local_context.update(item)

            if row_template:
                row_fragments.append(self._resolve_placeholders(row_template, local_context))
                continue

            rendered_item = item
            if isinstance(rendered_item, (dict, list)):
                rendered_item = json.dumps(rendered_item)
            row_fragments.append(f"<div>{html.escape(str(rendered_item))}</div>")

        return (
            f"<{wrapper_tag} class=\"{html.escape(wrapper_class)}\">"
            f"{''.join(row_fragments)}"
            f"</{wrapper_tag}>"
        )

    def _render_component(
        self,
        component: TemplateComponent,
        *,
        variables: dict[str, Any],
        options: dict[str, Any],
    ) -> str:
        component_json = component.component_json if isinstance(component.component_json, dict) else {}
        component_type = (component.component_type or "").strip().lower()

        condition_expression = str(component_json.get("condition") or "").strip()
        if condition_expression and not self._evaluate_condition(
            condition_expression,
            variables=variables,
            options=options,
        ):
            return ""

        context = dict(variables)

        if component_type in {"text", "paragraph", "title", "subtitle"}:
            text_value = str(component_json.get("text") or component_json.get("content") or "")
            tag = str(component_json.get("tag") or "p").strip().lower()
            rendered = self._resolve_placeholders(text_value, context)
            return f"<{tag}>{rendered}</{tag}>"

        if component_type in {"html", "rich_text"}:
            html_value = str(component_json.get("html") or component_json.get("content") or "")
            return self._resolve_placeholders(html_value, context)

        if component_type == "table":
            return self._render_table(component_json, context)

        if component_type == "image":
            return self._render_image(component_json, context)

        if component_type in {"qr", "qr_code"}:
            return self._render_qr_or_barcode(component_json=component_json, context=context, mode="qr")

        if component_type in {"barcode", "bar_code"}:
            return self._render_qr_or_barcode(component_json=component_json, context=context, mode="barcode")

        if component_type in {"dynamic", "dynamic_section", "repeat", "repeater"}:
            return self._render_dynamic_section(component_json, variables=variables, options=options)

        if component_type in {"conditional", "condition"}:
            true_html = str(component_json.get("true_html") or component_json.get("html") or "")
            false_html = str(component_json.get("false_html") or "")
            expression = str(component_json.get("expression") or component_json.get("condition") or "")
            matched = self._evaluate_condition(expression, variables=variables, options=options)
            chosen_html = true_html if matched else false_html
            return self._resolve_placeholders(chosen_html, context)

        fallback_value = component_json.get("content") or component_json.get("text") or component_json
        if isinstance(fallback_value, (dict, list)):
            fallback_value = json.dumps(fallback_value)
        rendered_fallback = self._resolve_placeholders(str(fallback_value), context)
        return f"<div>{rendered_fallback}</div>"

    def _render_conditional_blocks(
        self,
        blocks: list[dict[str, Any]],
        *,
        variables: dict[str, Any],
        options: dict[str, Any],
    ) -> str:
        fragments: list[str] = []
        for block in blocks:
            condition = str(block.get("condition") or "").strip()
            matched = self._evaluate_condition(condition, variables=variables, options=options)
            html_template = str(block.get("html") or "") if matched else str(block.get("else_html") or "")
            if html_template:
                fragments.append(self._resolve_placeholders(html_template, variables))
        return "".join(fragments)

    def render_template(
        self,
        *,
        template_code: str = "",
        template_version_code: str = "",
        template_version_id: Any = None,
        variables: Any = None,
        options: Any = None,
    ) -> dict[str, Any]:
        variables_dict = self._ensure_dict(variables, "variables")
        options_dict = self._ensure_dict(options, "options")

        template_version = self._resolve_template_version(
            template_code=(template_code or "").strip(),
            template_version_code=(template_version_code or "").strip(),
            template_version_id=template_version_id,
        )
        components = list(self.repository.get_template_components(template_version))
        style = self.repository.get_template_style(template_version)

        template_json = self._coerce_template_json(template_version.template_json)
        header_html = self._resolve_placeholders(str(template_json.get("header_html") or ""), variables_dict)
        footer_html = self._resolve_placeholders(str(template_json.get("footer_html") or ""), variables_dict)

        execution_log: list[dict[str, Any]] = []
        self._log(
            execution_log,
            stage="TEMPLATE_RENDER_START",
            message="Template rendering started.",
            metadata={
                "template_code": template_version.template.code,
                "template_version_code": template_version.code,
                "component_count": len(components),
            },
        )

        style_css = self._build_style_css(style)
        body_fragments: list[str] = []

        pm_doc = self._coerce_prosemirror_doc(template_json)
        body_html_template = self._prosemirror_doc_to_html(pm_doc, variables_dict)

        header_html = self._replace_variable_chip_spans(header_html, variables_dict)
        footer_html = self._replace_variable_chip_spans(footer_html, variables_dict)
        body_html_template = self._replace_variable_chip_spans(body_html_template, variables_dict)
        body_html_template = self._expand_repeat_tbody(body_html_template, variables_dict)
        if body_html_template:
            body_fragments.append(self._resolve_placeholders(body_html_template, variables_dict, escape_values=False))

        conditional_blocks = template_json.get("conditional_blocks")
        if conditional_blocks is not None:
            normalized_blocks = self._ensure_list(conditional_blocks, "conditional_blocks")
            typed_blocks = [item for item in normalized_blocks if isinstance(item, dict)]
            body_fragments.append(
                self._render_conditional_blocks(
                    typed_blocks,
                    variables=variables_dict,
                    options=options_dict,
                )
            )

        dynamic_sections = template_json.get("dynamic_sections")
        if dynamic_sections is not None:
            normalized_sections = self._ensure_list(dynamic_sections, "dynamic_sections")
            for section in normalized_sections:
                if isinstance(section, dict):
                    body_fragments.append(
                        self._render_dynamic_section(
                            section,
                            variables=variables_dict,
                            options=options_dict,
                        )
                    )

        for component in components:
            rendered = self._render_component(component, variables=variables_dict, options=options_dict)
            if not rendered:
                continue
            component_type = (component.component_type or "").strip().lower()
            if component_type == "header":
                header_html += rendered
                continue
            if component_type == "footer":
                footer_html += rendered
                continue
            body_fragments.append(rendered)

        rendered_body = "".join(body_fragments)
        html_output = (
            "<!DOCTYPE html>"
            "<html lang=\"en\">"
            "<head>"
            "<meta charset=\"utf-8\"/>"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"/>"
            f"<title>{html.escape(template_version.template.name)}</title>"
            f"<style>{style_css}</style>"
            "</head>"
            "<body>"
            "<div class=\"template-container\">"
            f"<header class=\"template-header\">{header_html}</header>"
            f"<main class=\"template-content\">{rendered_body}</main>"
            f"<footer class=\"template-footer\">{footer_html}</footer>"
            "</div>"
            "</body>"
            "</html>"
        )

        self._log(
            execution_log,
            stage="TEMPLATE_RENDER_COMPLETE",
            message="Template rendering completed.",
            metadata={
                "template_version": template_version.version_number,
                "html_length": len(html_output),
            },
        )

        return {
            "template_code": template_version.template.code,
            "template_name": template_version.template.name,
            "template_version_code": template_version.code,
            "template_version_number": template_version.version_number,
            "header_html": header_html,
            "footer_html": footer_html,
            "body_html": rendered_body,
            "html": html_output,
            "component_count": len(components),
            "execution_log": execution_log,
        }
