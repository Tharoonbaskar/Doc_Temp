from __future__ import annotations

import hashlib
import json
from typing import Any

from django.conf import settings
from django.core.cache import cache

from ..models import Template, TemplateVersion
from ..pdf_engine import EnterprisePDFEngine


class HtmlGenerator:
    def __init__(self, pdf_engine: EnterprisePDFEngine | None = None, cache_timeout_seconds: int = 300) -> None:
        self.pdf_engine = pdf_engine or EnterprisePDFEngine()
        self.cache_timeout_seconds = cache_timeout_seconds

    @staticmethod
    def _hash_payload(payload: dict[str, Any]) -> str:
        canonical = json.dumps(payload or {}, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _load_layout_options(self, template: Template) -> dict[str, Any]:
        css_cache_key = f"template-render:css-options:{template.id}:{template.page_size}:{template.page_orientation}"
        options = cache.get(css_cache_key)
        if options is not None:
            return dict(options)

        options = self.pdf_engine._normalize_layout_options(
            template,
            {
                "variable_resolution_mode": "KEEP_UNRESOLVED",
                "preview_unresolved": True,
            },
        )
        cache.set(css_cache_key, options, timeout=self.cache_timeout_seconds)
        return dict(options)

    def _cache_static_assets(self) -> None:
        assets_cache_key = "template-render:static-assets"
        assets = {
            "static_url": str(getattr(settings, "STATIC_URL", "") or ""),
            "media_url": str(getattr(settings, "MEDIA_URL", "") or ""),
        }
        cache.set(assets_cache_key, assets, timeout=self.cache_timeout_seconds)

    def generate(self, *, template: Template, template_version: TemplateVersion, payload: dict[str, Any]) -> dict[str, Any]:
        payload_hash = self._hash_payload(payload)
        cache_key = f"template-render:html:{template_version.id}:{payload_hash}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        self._cache_static_assets()
        options = self._load_layout_options(template)

        source_doc = self.pdf_engine._coerce_prosemirror_doc(template_version.template_json)
        resolved_doc, missing_tokens = self.pdf_engine._resolve_enterprise_variables(
            source_doc=source_doc,
            variables=payload,
            resolution_mode="KEEP_UNRESOLVED",
        )

        template_json = template_version.template_json if isinstance(template_version.template_json, dict) else {}
        variable_index = self.pdf_engine._flatten_variables(payload)

        header_missing: set[str] = set()
        header_template = options.get("header_html") or str(template_json.get("header_html") or "")
        footer_template = options.get("footer_html") or str(template_json.get("footer_html") or "")

        resolved_header = self.pdf_engine._resolve_html_template(
            header_template,
            variables=payload,
            variable_index=variable_index,
            missing_tokens=header_missing,
            resolution_mode="KEEP_UNRESOLVED",
        )
        resolved_footer = self.pdf_engine._resolve_html_template(
            footer_template,
            variables=payload,
            variable_index=variable_index,
            missing_tokens=header_missing,
            resolution_mode="KEEP_UNRESOLVED",
        )

        avg_margin_mm = (
            options["margin_top_mm"]
            + options["margin_bottom_mm"]
            + options["margin_left_mm"]
            + options["margin_right_mm"]
        ) / 4.0
        margin_px = avg_margin_mm * (96.0 / 25.4)

        paginated_doc = self.pdf_engine._auto_paginate_doc(
            resolved_doc,
            page_size=options["page_size"],
            orientation=options["orientation"],
            margin_px=margin_px,
        )
        pages = self.pdf_engine._split_pages(paginated_doc)

        html_document = self.pdf_engine._build_html_document(
            pages=pages,
            template=template,
            template_version=template_version,
            options=options,
            resolved_header_html=resolved_header,
            resolved_footer_html=resolved_footer,
        )

        result = {
            "html": html_document,
            "missing_variables": sorted(set(missing_tokens).union(header_missing)),
        }
        cache.set(cache_key, result, timeout=self.cache_timeout_seconds)
        return result
