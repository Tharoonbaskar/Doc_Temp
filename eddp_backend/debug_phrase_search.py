from pprint import pprint

from apps.templates.models import TemplateVersion, TemplateElementChange

PHRASE = (
    "We are please to inform you that your loan application "
    "has been approved .Your loan amount of"
)

phrase = PHRASE.lower()

print("=" * 100)
print("SEARCHING TEMPLATE VERSIONS")
print("=" * 100)

version_hits = []

for v in TemplateVersion.objects.all().order_by("template_id", "version_number"):
    text = str(v.template_json or "").lower()

    if phrase in text:
        version_hits.append(
            {
                "template_id": str(v.template_id),
                "version": v.version_number,
                "status": v.version_status,
            }
        )

print(f"Found {len(version_hits)} matching version(s)\n")
pprint(version_hits)

print("\n" + "=" * 100)
print("SEARCHING ELEMENT CHANGES")
print("=" * 100)

change_hits = []

for c in (
    TemplateElementChange.objects
    .select_related("version")
    .all()
):
    old_text = str(c.old_value or "").lower()
    new_text = str(c.new_value or "").lower()

    if phrase in old_text or phrase in new_text:
        change_hits.append(
            {
                "template_id": str(c.version.template_id),
                "version": c.version.version_number,
                "change_id": str(c.id),
                "change_type": c.change_type,
                "approval_status": c.approval_status,
                "element_id": c.element_id,
            }
        )

print(f"Found {len(change_hits)} matching change(s)\n")
pprint(change_hits)

print("\n" + "=" * 100)
print("DONE")
print("=" * 100)