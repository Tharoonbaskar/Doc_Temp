# Canvas → Tiptap Migration - Quick Start Guide

## 🚨 Current Status: MIGRATION IN PROGRESS

Your Enterprise Dynamic Document Platform is **partially migrated** from Canvas/Figma architecture to Tiptap/ProseMirror. The new editor works, but **significant legacy code remains active**.

---

## 📋 Top 5 Critical Issues

### 1. ❌ Word Import Creates Canvas Elements
**File:** `eddp_backend/apps/templates/parsers.py`  
**Problem:** DOCX import generates x/y coordinate-based elements, not ProseMirror JSON  
**Impact:** Imported documents incompatible with new architecture  
**Action:** Rewrite parser to output ProseMirror JSON

### 2. ❌ Legacy Conversion Functions Still Active
**File:** `eddp_frontend/src/features/templates/components/TemplateForm.tsx`  
**Functions:**
- `extractLegacyElementsFromContentJson()`
- `legacyElementsToHtml()`
- `htmlToLegacyElements()`

**Problem:** Actively converts between Canvas and ProseMirror  
**Action:** Delete these functions, use Tiptap's built-in methods

### 3. ❌ DesignerElement Type Defines Canvas Properties
**File:** `eddp_frontend/src/features/templates/components/TemplateForm.tsx` (lines 130-170)  
**Problem:** Type defines x, y, width, height, rotation, zIndex (Canvas concepts)  
**Action:** Replace with ProseMirror node types

### 4. ❌ Position-Based Change Detection
**File:** `eddp_backend/apps/templates/diff_utils.py`  
**Problem:** Tracks `POSITION_CHANGED` by comparing x/y coordinates  
**Action:** Remove position tracking, focus on semantic changes

### 5. ❌ SelectionContext Expects Canvas Elements
**File:** `eddp_frontend/src/features/templates/contexts/SelectionContext.tsx`  
**Problem:** Uses `DesignerElement[]` array instead of ProseMirror selection  
**Action:** Integrate with ProseMirror Selection API

---

## ✅ What's Working Correctly

- ✅ **Tiptap Editor** - Fully functional
- ✅ **Track Changes Extension** - Uses ProseMirror decorations properly
- ✅ **Content Canonicalization** - Backend normalizes to ProseMirror format
- ✅ **DeepDiff** - Semantic comparison working

---

## 🎯 Immediate Actions (Phase 1 - P0)

### Day 1: Stop Creating Canvas Elements
```bash
# 1. Delete legacy converters
# File: eddp_frontend/src/features/templates/components/TemplateForm.tsx
# Remove lines 413-500 (extractLegacyElementsFromContentJson, legacyElementsToHtml, htmlToLegacyElements)

# 2. Fix Word Import
# File: eddp_backend/apps/templates/parsers.py
# Rewrite WordDocumentParser to output:
{
  "prosemirror_json": {
    "type": "doc",
    "content": [...]
  }
}
```

### Day 2: Type System Cleanup
```bash
# 3. Remove DesignerElement interface
# File: eddp_frontend/src/features/templates/components/TemplateForm.tsx
# Replace with ProseMirror types

# 4. Update SelectionContext
# File: eddp_frontend/src/features/templates/contexts/SelectionContext.tsx
# Use editor.state.selection instead of element arrays
```

### Day 3: Data Migration
```bash
# 5. Create migration script
cd eddp_backend
python manage.py makemigrations templates --name convert_canvas_to_prosemirror --empty

# In migration file, scan all Template.content_json fields
# Convert any Canvas element arrays to ProseMirror JSON
```

---

## 🔍 How to Identify Legacy Code

Search for these patterns:

### Frontend (TypeScript/React)
```bash
# Canvas element arrays
grep -r "DesignerElement\[\]" eddp_frontend/src/

# Coordinate properties
grep -r "\.x\s*:" eddp_frontend/src/features/templates/
grep -r "\.y\s*:" eddp_frontend/src/features/templates/

# Legacy converters
grep -r "legacyElementsTo" eddp_frontend/src/
```

### Backend (Python/Django)
```bash
# Canvas element generation
grep -r "x_position\|y_position" eddp_backend/apps/templates/

# Position change tracking
grep -r "POSITION_CHANGED" eddp_backend/apps/templates/

# Canvas terminology
grep -r "canvas" eddp_backend/apps/templates/
```

---

## 📊 Migration Progress Tracker

| Component | Status | Priority | Owner |
|-----------|--------|----------|-------|
| Word Import Parser | ❌ Legacy | P0 | Backend Team |
| Legacy Converters | ❌ Active | P0 | Frontend Team |
| DesignerElement Type | ❌ Active | P0 | Frontend Team |
| SelectionContext | ❌ Canvas | P0 | Frontend Team |
| Diff Utils Position Tracking | ❌ Active | P1 | Backend Team |
| Database Field Names | ⚠️ Unclear | P1 | Backend Team |
| Data Migration | ❌ Missing | P0 | Backend Team |
| Review UI | ⚠️ Unknown | P1 | Frontend Team |
| PDF Rendering | ⚠️ Unknown | P2 | Backend Team |
| Word Export | ⚠️ Unknown | P2 | Backend Team |

**Legend:**
- ❌ Legacy/Broken
- ⚠️ Needs Audit
- ✅ Compliant

---

## 🚀 Quick Wins (Easy Fixes)

1. **Delete unused Canvas references** (15 min)
   - Remove PAGE_DIMENSIONS constant (not needed for editor)
   - Delete legacy converter functions
   
2. **Update comments** (30 min)
   - Change "designer elements" → "ProseMirror nodes"
   - Change "canvas JSON" → "ProseMirror JSON"
   
3. **Fix API response** (1 hour)
   - `import_word` endpoint should return `{prosemirror_json: {...}}`

4. **Rename database fields** (2 hours)
   - `content_json` → `prosemirror_json` (with migration)

---

## 📖 Architecture Reference

### OLD (Canvas/Figma)
```
Document = Array<DesignerElement>

DesignerElement = {
  id, type, x, y, width, height, 
  rotation, zIndex, groupId,
  text, ...
}

Rendering: Sort by (page, y) → Generate HTML
```

### NEW (Tiptap/ProseMirror)
```
Document = ProseMirror JSON

{
  "prosemirror_json": {
    "type": "doc",
    "content": [
      {
        "type": "heading",
        "attrs": {...},
        "content": [...]
      },
      ...
    ]
  }
}

Rendering: ProseMirror → HTML (built-in)
```

---

## 🛠️ Development Commands

### Audit Codebase
```bash
# Find all Canvas element references
grep -r "DesignerElement" eddp_frontend/src/ | wc -l

# Find coordinate usage
grep -rE "\.(x|y|width|height)\s*:" eddp_frontend/src/features/templates/ | wc -l

# Find legacy functions
grep -r "legacy" eddp_frontend/src/features/templates/
```

### Test Migration
```bash
# Backend
cd eddp_backend
python manage.py test apps.templates.tests

# Frontend
cd eddp_frontend
npm test -- TemplateForm
```

---

## 📞 Support

- **Full Audit Report:** `CANVAS_TO_TIPTAP_MIGRATION_AUDIT.md`
- **Architecture Diagrams:** (to be created)
- **Migration Runbook:** (to be created)

---

**Last Updated:** 2026-07-17  
**Next Review:** After Phase 1 completion  
**Estimated Completion:** 2-4 weeks
