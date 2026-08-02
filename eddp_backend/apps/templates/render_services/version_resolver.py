from __future__ import annotations

from django.core.cache import cache

from apps.common.choices import VersionStatusChoices
from apps.common.exceptions import ValidationException

from ..models import Template, TemplateVersion


class VersionResolver:
    def __init__(self, cache_timeout_seconds: int = 300) -> None:
        self.cache_timeout_seconds = cache_timeout_seconds

    def resolve_latest_approved(self, template: Template) -> TemplateVersion:
        cache_key = f"template-render:approved-version-id:{template.id}"
        version_id = cache.get(cache_key)

        queryset = TemplateVersion.objects.filter(template=template)
        version = queryset.filter(id=version_id).first() if version_id else None

        if version is None or version.version_status != VersionStatusChoices.APPROVED:
            version = queryset.filter(
                version_status=VersionStatusChoices.APPROVED,
            ).order_by("-version_number", "-approved_at", "-updated_at").first()

            if version is None:
                raise ValidationException(detail="No approved template version available.")

            cache.set(cache_key, str(version.id), timeout=self.cache_timeout_seconds)

        return version
