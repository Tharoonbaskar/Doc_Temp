import os
from pathlib import Path

# Bootstrap Django settings for standalone script execution.
project_root = Path(__file__).parent
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from apps.runtime.services.pdf_generator import PDFGeneratorService
from apps.templates.pdf_engine import EnterprisePDFEngine

html = "<html><body><p>test</p></body></html>"

b1 = PDFGeneratorService._render_pdf_bytes(html)
b2 = EnterprisePDFEngine()._render_pdf_bytes(html)

print("runtime_pdf_generator_bytes:", len(b1))
print("enterprise_pdf_engine_bytes:", len(b2))