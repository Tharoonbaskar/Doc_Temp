from pprint import pprint

from apps.templates.models import (
    Template,
    TemplateVersion,
    TemplateElementChange,
)

TEMPLATE_ID = "4156ce4a-b871-407c-85aa-d72093a7939d"

print("=" * 100)
print("TEMPLATE")
print("=" * 100)

t = Template.objects.get(id=TEMPLATE_ID)

print("ID              :", t.id)
print("Name            :", t.name)
print("Current Version :", getattr(t, "current_version", None))
print("Content Nodes   :", len((t.prosemirror_json or {}).get("content", [])))

print("\nCurrent Template JSON")
pprint(t.prosemirror_json)

print("\n" + "=" * 100)
print("VERSIONS")
print("=" * 100)

versions = (
    TemplateVersion.objects
    .filter(template=t)
    .order_by("version_number")
)

for v in versions:
    print(
        f"Version={v.version_number} "
        f"Status={v.version_status} "
        f"Base={v.base_version_id}"
    )

print("\n" + "=" * 100)
print("VERSION 2")
print("=" * 100)

v2 = TemplateVersion.objects.get(
    template=t,
    version_number=2,
)

print("Version Number :", v2.version_number)
print("Status         :", v2.version_status)
print("Base Version   :", v2.base_version_id)

print("\nTemplate JSON")
pprint(v2.template_json)

print("\n" + "=" * 100)
print("ELEMENT CHANGES")
print("=" * 100)

changes = (
    TemplateElementChange.objects
    .filter(version=v2)
    .order_by("created_at")
)

print("Total Changes:", changes.count())

for i, c in enumerate(changes, start=1):
    print("\n" + "-" * 100)
    print(f"CHANGE #{i}")
    print("-" * 100)

    print("ID              :", c.id)
    print("Change Type     :", c.change_type)
    print("Approval Status :", c.approval_status)
    print("Element ID      :", c.element_id)

    old_sem = None
    if isinstance(c.old_value, dict):
        old_sem = c.old_value.get("_semantic", {}).get("type")

    new_sem = None
    if isinstance(c.new_value, dict):
        new_sem = c.new_value.get("_semantic", {}).get("type")

    print("Old Semantic :", old_sem)
    print("New Semantic :", new_sem)

    print("\nOLD VALUE")
    pprint(c.old_value)

    print("\nNEW VALUE")
    pprint(c.new_value)

print("\n" + "=" * 100)
print("DONE")
print("=" * 100)