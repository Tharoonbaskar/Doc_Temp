import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.templates.models import Template
from apps.templates.serializers import TemplateSerializer

t = Template.objects.first()
serializer = TemplateSerializer(t)
data = serializer.data

print("API Response Data:")
print(f"  has_pending_draft: {data.get('has_pending_draft')}")
print(f"  pending_draft_version: {data.get('pending_draft_version')}")
print(f"  status: {data.get('status')}")
print(f"  current_version: {data.get('current_version')}")
print(f"  version_count: {data.get('version_count')}")
