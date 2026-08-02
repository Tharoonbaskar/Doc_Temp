from apps.templates.models import Template, TemplateVersion
from apps.templates.services import TemplateService

tid = "9ddccbb4-a956-4306-b09b-84def1e91df0"

t = Template.objects.filter(id=tid).first()
print("template", t.name if t else None)

v = TemplateVersion.objects.filter(
    template=t,
    version_number=2
).first()

print("version", v.version_number if v else None,
      v.version_status if v else None)
print("base_version", getattr(v, "base_version_id", None) if v else None)

if t and v:
    response = TemplateService().get_version_changes(str(t.id), v.version_number)
    print("reconcile_status", response.status_code)
    v.refresh_from_db()
    print("base_version_after", v.base_version_id)

changes = list(v.element_changes.all()) if v else []
print("total", len(changes))

summary = {}
status_summary = {}
dedup_summary = {}

for c in changes:
    sem = {}
    if isinstance(c.new_value, dict):
        sem = c.new_value.get("_semantic", {})
    elif isinstance(c.old_value, dict):
        sem = c.old_value.get("_semantic", {})

    semantic_type = sem.get("type") or "UNKNOWN"
    summary[semantic_type] = summary.get(semantic_type, 0) + 1
    status_summary[c.approval_status] = status_summary.get(c.approval_status, 0) + 1
    node_id = sem.get("nodeId") or sem.get("elementId") or c.element_id
    page = sem.get("page") or ""
    dedup_key = f"{c.change_type}|{semantic_type}|{node_id}|{page}"
    dedup_summary[dedup_key] = dedup_summary.get(dedup_key, 0) + 1

    print(
        c.id,
        c.change_type,
        c.approval_status,
        semantic_type,
        node_id,
        c.element_id,
    )

print("summary", summary)
print("status_summary", status_summary)
print("dedup_total", len(dedup_summary))
print("dedup_summary", dedup_summary)