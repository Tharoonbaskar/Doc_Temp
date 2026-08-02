import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.templates.models import Template

t = Template.objects.first()
print(f"Template: {t.name}")
print(f"has_pending_draft property exists: {hasattr(t, 'has_pending_draft')}")
print(f"has_pending_draft value: {t.has_pending_draft}")
print(f"pending_draft_version: {t.pending_draft_version}")

# Check versions
print("\nVersions:")
for v in t.versions.all().order_by('version_number'):
    print(f"  v{v.version_number}: {v.version_name} | status={v.version_status}")
