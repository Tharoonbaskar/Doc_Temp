# Generated data migration to extract prosemirror_json from content_json

from django.db import migrations
import json


def migrate_content_to_prosemirror(apps, schema_editor):
    """Extract prosemirror_json from composite content_json format"""
    Template = apps.get_model('templates', 'Template')
    
    for template in Template.objects.all():
        try:
            if not template.content_json:
                continue
                
            content = json.loads(template.content_json)
            
            # Extract ProseMirror JSON
            pm_json = None
            if isinstance(content, dict):
                pm_json = content.get('prosemirror_json')
                if not pm_json:
                    # Try alternative keys
                    pm_json = content.get('pm_json') or content.get('doc') or content.get('tiptap_json')
                
                # Extract page settings
                page = content.get('page', {})
                if isinstance(page, dict):
                    if page.get('size'):
                        template.page_size = str(page['size']).upper()
                    if page.get('orientation'):
                        template.page_orientation = str(page['orientation']).upper()
            
            if pm_json and isinstance(pm_json, dict) and pm_json.get('type') == 'doc':
                template.prosemirror_json = pm_json
            else:
                # Default empty document
                template.prosemirror_json = {"type": "doc", "content": [{"type": "paragraph"}]}
            
            template.save(update_fields=['prosemirror_json', 'page_size', 'page_orientation'])
            
        except Exception as e:
            print(f"Migration error for template {template.id}: {e}")


def reverse_migration(apps, schema_editor):
    """Reverse is not needed - content_json still exists"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('templates', '0006_add_prosemirror_fields'),
    ]

    operations = [
        migrations.RunPython(migrate_content_to_prosemirror, reverse_migration),
    ]
