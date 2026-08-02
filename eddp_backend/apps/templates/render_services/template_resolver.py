from __future__ import annotations

from django.core.cache import cache

from apps.common.exceptions import ResourceNotFoundException

from ..models import Template


class TemplateResolver:
    def __init__(self, cache_timeout_seconds: int = 300) -> None:
        self.cache_timeout_seconds = cache_timeout_seconds

    def resolve(self, template_code: str) -> Template:
        normalized_code = str(template_code or "").strip().upper()
        if not normalized_code:
            raise ResourceNotFoundException(detail="Template not found.")

        cache_key = f"template-render:template-id:{normalized_code}"
        template_id = cache.get(cache_key)

        queryset = Template.objects.select_related("document")
        template = queryset.filter(id=template_id).first() if template_id else None
        if template is None:
            template = queryset.filter(code=normalized_code).first()
            if template is None:
                raise ResourceNotFoundException(detail="Template not found.")
            cache.set(cache_key, str(template.id), timeout=self.cache_timeout_seconds)

        return template
