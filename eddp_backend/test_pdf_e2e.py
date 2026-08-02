"""
End-to-End PDF Generation Test Script

This script tests the complete PDF generation pipeline:
1. WeasyPrint dependency check
2. Template retrieval
3. PDF preview generation (base64)
4. PDF file generation (saved to disk)
5. PDF download verification
"""

import os
import sys
import base64
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from apps.common.utils import configure_weasyprint_runtime, get_weasyprint_runtime_warnings
from apps.templates.pdf_service import TemplatePDFService
from apps.templates.models import Template, TemplateVersion
from apps.common.choices import TemplateStatusChoices, VersionStatusChoices


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 80)
    print(title.center(80))
    print("=" * 80 + "\n")


def test_weasyprint_dependencies():
    """Test WeasyPrint native dependencies."""
    print_header("1. WEASYPRINT DEPENDENCY CHECK")
    
    print("Configuring WeasyPrint runtime...")
    configured_dirs = configure_weasyprint_runtime()
    warnings = get_weasyprint_runtime_warnings()
    
    if configured_dirs:
        print(f"✓ Configured directories: {', '.join(configured_dirs)}")
    else:
        print("✗ No GTK directories configured")
    
    if warnings:
        print(f"⚠ Warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    try:
        from weasyprint import HTML, __version__
        print(f"✓ WeasyPrint {__version__} imported successfully")
        
        # Test basic rendering
        test_html = "<html><body><h1>Test</h1></body></html>"
        test_pdf = HTML(string=test_html).write_pdf()
        print(f"✓ Test PDF rendered successfully ({len(test_pdf)} bytes)")
        return True
    except Exception as exc:
        print(f"✗ WeasyPrint import/render failed: {exc}")
        return False


def test_template_availability():
    """Check if test templates are available."""
    print_header("2. TEMPLATE AVAILABILITY CHECK")
    
    templates = Template.objects.filter(
        status=TemplateStatusChoices.APPROVED
    ).select_related('document')
    
    print(f"Found {templates.count()} approved template(s)")
    
    if not templates.exists():
        print("✗ No approved templates found. Creating test template...")
        # You can add template creation logic here if needed
        return None
    
    for template in templates[:5]:
        approved_versions = TemplateVersion.objects.filter(
            template=template,
            version_status=VersionStatusChoices.APPROVED
        ).count()
        print(f"  • {template.code} - {template.name} ({approved_versions} approved version(s))")
    
    # Return first template for testing
    first_template = templates.first()
    print(f"\n✓ Using template: {first_template.code} - {first_template.name}")
    return first_template


def test_pdf_preview(template_id: str):
    """Test PDF preview generation (base64 encoded)."""
    print_header("3. PDF PREVIEW TEST")
    
    service = TemplatePDFService()
    
    payload = {
        "pdf_options": {
            "variable_resolution_mode": "KEEP_UNRESOLVED",
            "preview_unresolved": True,
        }
    }
    
    print(f"Generating PDF preview for template: {template_id}")
    start_time = datetime.now()
    
    try:
        response = service.preview_pdf(
            request=None,
            template_id=template_id,
            payload=payload,
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if response.status_code == 200:
            data = response.data.get('data', {})
            preview_b64 = data.get('preview_base64', '')
            page_count = data.get('page_count', 0)
            missing_vars = data.get('missing_variables', [])
            warnings = data.get('warnings', [])
            
            print(f"✓ Preview generated successfully in {duration:.2f}s")
            print(f"  • Template: {data.get('template_code')} v{data.get('approved_version')}")
            print(f"  • Pages: {page_count}")
            print(f"  • PDF size: {len(base64.b64decode(preview_b64)):,} bytes")
            print(f"  • Missing variables: {len(missing_vars)}")
            
            if missing_vars:
                print(f"    - {', '.join(missing_vars[:5])}")
                if len(missing_vars) > 5:
                    print(f"    - ... and {len(missing_vars) - 5} more")
            
            if warnings:
                print(f"  ⚠ Warnings: {len(warnings)}")
                for warning in warnings[:3]:
                    print(f"    - {warning}")
            
            return preview_b64
        else:
            print(f"✗ Preview failed with status {response.status_code}")
            print(f"  Error: {response.data}")
            return None
            
    except Exception as exc:
        print(f"✗ Exception during preview: {exc}")
        import traceback
        traceback.print_exc()
        return None


def test_pdf_generation(template_id: str):
    """Test PDF file generation and storage."""
    print_header("4. PDF GENERATION TEST")
    
    service = TemplatePDFService()
    
    payload = {
        "pdf_options": {
            "variable_resolution_mode": "KEEP_UNRESOLVED",
        },
        "file_name": f"test_pdf_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    }
    
    print(f"Generating PDF file for template: {template_id}")
    start_time = datetime.now()
    
    try:
        response = service.generate_pdf(
            request=None,
            template_id=template_id,
            payload=payload,
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if response.status_code == 200:
            data = response.data.get('data', {})
            file_name = data.get('file_name')
            file_path = data.get('file_path')
            file_size = data.get('file_size', 0)
            page_count = data.get('page_count', 0)
            
            print(f"✓ PDF generated successfully in {duration:.2f}s")
            print(f"  • File: {file_name}")
            print(f"  • Path: {file_path}")
            print(f"  • Size: {file_size:,} bytes")
            print(f"  • Pages: {page_count}")
            
            # Verify file exists
            if file_path:
                from django.conf import settings
                full_path = Path(settings.MEDIA_ROOT) / file_path
                if full_path.exists():
                    actual_size = full_path.stat().st_size
                    print(f"  ✓ File verified on disk ({actual_size:,} bytes)")
                else:
                    print(f"  ✗ File not found at {full_path}")
            
            return data
        else:
            print(f"✗ Generation failed with status {response.status_code}")
            print(f"  Error: {response.data}")
            return None
            
    except Exception as exc:
        print(f"✗ Exception during generation: {exc}")
        import traceback
        traceback.print_exc()
        return None


def test_pdf_download(template_id: str):
    """Test PDF download endpoint."""
    print_header("5. PDF DOWNLOAD TEST")
    
    service = TemplatePDFService()
    
    print(f"Testing download for template: {template_id}")
    
    try:
        response = service.download_pdf(
            request=None,
            template_id=template_id,
        )
        
        if isinstance(response, django.http.HttpResponse):
            content_type = response.get('Content-Type', '')
            content_disposition = response.get('Content-Disposition', '')
            content_length = len(response.content)
            
            print(f"✓ Download successful")
            print(f"  • Content-Type: {content_type}")
            print(f"  • Content-Disposition: {content_disposition}")
            print(f"  • Size: {content_length:,} bytes")
            
            # Save to temp file for verification
            temp_file = Path(project_root) / "test_download.pdf"
            temp_file.write_bytes(response.content)
            print(f"  ✓ Saved test file: {temp_file}")
            
            return True
        else:
            print(f"✗ Download returned non-HttpResponse")
            return False
            
    except Exception as exc:
        print(f"✗ Exception during download: {exc}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all end-to-end tests."""
    print_header("PDF GENERATION END-TO-END TEST SUITE")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'dependencies': False,
        'template': False,
        'preview': False,
        'generation': False,
        'download': False,
    }
    
    # Test 1: Dependencies
    results['dependencies'] = test_weasyprint_dependencies()
    if not results['dependencies']:
        print("\n❌ CRITICAL: WeasyPrint dependencies not available.")
        print("Please run the installation script first:")
        print("  powershell -ExecutionPolicy Bypass -File install_gtk_for_weasyprint.ps1")
        print("\nOr follow the manual setup guide in setup_weasyprint_windows.md")
        return
    
    # Test 2: Template availability
    test_template = test_template_availability()
    if test_template is None:
        print("\n❌ CRITICAL: No approved templates found for testing.")
        return
    results['template'] = True
    
    template_id = str(test_template.id)
    
    # Test 3: Preview
    preview_result = test_pdf_preview(template_id)
    results['preview'] = preview_result is not None
    
    # Test 4: Generation
    generation_result = test_pdf_generation(template_id)
    results['generation'] = generation_result is not None
    
    # Test 5: Download
    results['download'] = test_pdf_download(template_id)
    
    # Summary
    print_header("TEST RESULTS SUMMARY")
    
    all_passed = all(results.values())
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name.upper()}")
    
    print()
    if all_passed:
        print("🎉 ALL TESTS PASSED! PDF generation is working end-to-end.")
    else:
        print("⚠️  SOME TESTS FAILED. Please review the output above.")
    
    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
