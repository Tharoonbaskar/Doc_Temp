# PDF Generation - Quick Reference Guide

## Setup Status

### ✅ What's Already Implemented

The PDF generation system is **fully implemented** with:

1. **PDF Engine** (`apps/templates/pdf_engine.py`)
   - ProseMirror to HTML conversion
   - Enterprise variable resolution
   - WeasyPrint integration for PDF rendering
   - Post-processing (page counting, metadata injection)

2. **PDF Service** (`apps/templates/pdf_service.py`)
   - `preview_pdf()` - Returns base64-encoded PDF
   - `generate_pdf()` - Generates and saves PDF file
   - `download_pdf()` - Streams PDF for download
   - Full audit logging and error handling

3. **API Endpoints** (automatically available)
   - `POST /api/templates/{id}/preview-pdf` - Preview PDF
   - `POST /api/templates/{id}/generate-pdf` - Generate PDF
   - `GET /api/templates/{id}/download-pdf` - Download PDF

4. **Utilities** (`apps/common/utils.py`)
   - WeasyPrint runtime auto-configuration
   - GTK dependency validation
   - Windows DLL path management

### ❌ What's Missing

**WeasyPrint native dependencies** (GTK/Pango/Cairo) are not installed or incompatible.

## Quick Fix

### Option 1: Automated Installation (Recommended)

Run as administrator:
```cmd
powershell -ExecutionPolicy Bypass -File install_gtk_for_weasyprint.ps1
```

### Option 2: Manual Installation

1. Download and install MSYS2 from https://www.msys2.org/
2. Open MSYS2 MINGW64 terminal
3. Run:
   ```bash
   pacman -Syu
   pacman -S mingw-w64-x86_64-gtk3 mingw-w64-x86_64-pango mingw-w64-x86_64-cairo
   ```
4. Add to system PATH: `C:\msys64\mingw64\bin`
5. Restart your terminal and Django server

### Option 3: Environment Variable Only

If MSYS2 is already installed, just set:
```cmd
set WEASYPRINT_DLL_DIRECTORIES=C:\msys64\mingw64\bin
```

## Testing

### Quick Test
```cmd
cd eddp_backend
python test_pdf_e2e.py
```

### Manual Test
```cmd
cd eddp_backend
python debug_pdf.py
```

### Test via API

**Preview PDF:**
```bash
curl -X POST http://localhost:8000/api/templates/{template-id}/preview-pdf \
  -H "Content-Type: application/json" \
  -d '{"pdf_options": {"variable_resolution_mode": "KEEP_UNRESOLVED"}}'
```

**Generate PDF:**
```bash
curl -X POST http://localhost:8000/api/templates/{template-id}/generate-pdf \
  -H "Content-Type: application/json" \
  -d '{"file_name": "my_document.pdf"}'
```

**Download PDF:**
```bash
curl -X GET http://localhost:8000/api/templates/{template-id}/download-pdf \
  --output document.pdf
```

## API Usage Examples

### Preview PDF (Returns Base64)

**Request:**
```http
POST /api/templates/a6249c24-1130-49e5-ba50-5416f3d37451/preview-pdf
Content-Type: application/json

{
  "version": "v1.0",
  "variables": {
    "applicant_name": "John Doe",
    "loan_amount": "50000"
  },
  "pdf_options": {
    "variable_resolution_mode": "KEEP_UNRESOLVED",
    "preview_unresolved": true
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "template_name": "Loan Application",
    "template_code": "LOAN-001",
    "approved_version": "v1.0",
    "page_count": 3,
    "preview_base64": "JVBERi0xLjQKJeLjz9...",
    "mime_type": "application/pdf",
    "missing_variables": ["guarantor_name"],
    "warnings": []
  }
}
```

### Generate PDF (Saves to Storage)

**Request:**
```http
POST /api/templates/a6249c24-1130-49e5-ba50-5416f3d37451/generate-pdf
Content-Type: application/json

{
  "file_name": "loan_application_john_doe.pdf",
  "variables": {
    "applicant_name": "John Doe",
    "loan_amount": "50000",
    "guarantor_name": "Jane Smith"
  }
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "template_name": "Loan Application",
    "file_name": "loan_application_john_doe.pdf",
    "file_path": "generated-template-pdfs/loan-001/loan_application_john_doe.pdf",
    "file_size": 245678,
    "page_count": 3,
    "download_url": "/api/templates/.../download-pdf",
    "file_url": "/media/generated-template-pdfs/..."
  }
}
```

### Download PDF

**Request:**
```http
GET /api/templates/a6249c24-1130-49e5-ba50-5416f3d37451/download-pdf?version=v1.0
```

**Response:**
Binary PDF file with headers:
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="loan-001-v1.0.pdf"
```

## Variable Resolution Modes

### `RESOLVE_STRICT` (Default)
- All variables must be provided
- Missing variables cause validation error
- Use for production document generation

### `KEEP_UNRESOLVED`
- Missing variables are rendered as placeholders
- No validation errors
- Use for previews and drafts

## Troubleshooting

### Error: "WeasyPrint dependencies are unavailable"
**Solution:** Install GTK using the installation script above.

### Error: "missing required symbol 'pango_context_set_round_glyph_positions'"
**Solution:** Your GTK runtime is outdated. Use MSYS2 version instead.

### Error: "Template not found"
**Solution:** Ensure the template exists and has status `APPROVED`.

### Error: "No approved template version is available"
**Solution:** At least one template version must have status `APPROVED`.

### PDF is blank or malformed
**Check:**
1. Template JSON structure is valid ProseMirror document
2. All required variables are provided (or use `KEEP_UNRESOLVED`)
3. Check server logs for rendering warnings

## Files

- `test_pdf_e2e.py` - Complete end-to-end test suite
- `debug_pdf.py` - Quick debug script
- `install_gtk_for_weasyprint.ps1` - Automated GTK installer
- `setup_weasyprint_windows.md` - Detailed setup guide
- `setup_and_test_pdf.bat` - One-click setup and test

## Next Steps

1. ✅ Install GTK dependencies
2. ✅ Run `test_pdf_e2e.py` to verify
3. ✅ Test API endpoints
4. ✅ Integrate into your application
