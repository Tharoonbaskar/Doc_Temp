from pprint import pprint

from apps.templates.pdf_service import TemplatePDFService

svc = TemplatePDFService()

print("=" * 80)
print("PREVIEW")
print("=" * 80)

resp = svc.preview_pdf(
    request=None,
    template_id="a6249c24-1130-49e5-ba50-5416f3d37451",
    payload={
        "pdf_options": {
            "variable_resolution_mode": "KEEP_UNRESOLVED",
            "preview_unresolved": True,
        }
    },
)

print("STATUS:", resp.status_code)
pprint(resp.data)

print()
print("=" * 80)
print("GENERATE")
print("=" * 80)

resp = svc.generate_pdf(
    request=None,
    template_id="a6249c24-1130-49e5-ba50-5416f3d37451",
    payload={
        "pdf_options": {
            "variable_resolution_mode": "KEEP_UNRESOLVED",
        }
    },
)

print("STATUS:", resp.status_code)
pprint(resp.data)