# Enterprise Architectural Audit Report
# Canvas/Figma Editor → Tiptap/ProseMirror Migration

**Date:** 2026-07-17  
**Status:** Migration In Progress (Partially Complete)  
**Objective:** Identify and document all legacy Canvas/Figma architecture dependencies

---

## Executive Summary

The Enterprise Dynamic Document Platform (EDDP) has begun migration from a **Canvas/Figma-style editor** (coordinate-based, absolutely positioned elements) to a **Tiptap/ProseMirror editor** (document-flow based, structured content).

**Current State:** The migration is **PARTIALLY COMPLETE**. The Tiptap editor is implemented and functional, but **significant legacy Canvas architecture remains embedded** throughout the codebase.

**Critical Issues:**
1. **Dual Data Models Coexist** - Both `DesignerElement[]` (Canvas) and `prosemirror_json` (Tiptap) representations exist
2. **Legacy Conversion Logic** - Active code still converts between Canvas elements and ProseMirror
3. **Position-Based Change Detection** - Diff utilities still track x/y coordinate changes
4. **Word Import Creates Canvas Elements** - DOCX parser generates coordinate-based elements, not ProseMirror
5. **Type System Confusion** - `DesignerElement` interface defines Canvas properties used by non-Canvas components

---

## 1. FRONTEND AUDIT - Canvas/Positioning Code

### 1.1 Legacy Type Definitions

**File:** `eddp_frontend/src/features/templates/components/TemplateForm.tsx`  
**Lines:** 130-170

**Current Implementation:**
```typescript
interface DesignerElement {
  id: string;
  type: DesignerElementType;
  label: string;
  page: number;
  x: number;              // ❌ LEGACY: Absolute X coordinate
  y: number;              // ❌ LEGACY: Absolute Y coordinate
  width: number;          // ❌ LEGACY: Fixed width
  height: number;         // ❌ LEGACY: Fixed height
  rotation: number;       // ❌ LEGACY: Canvas rotation
  opacity: number;        // ❌ LEGACY: Canvas opacity
  zIndex: number;         // ❌ LEGACY: Canvas layering
  groupId: string | null; // ❌ LEGACY: Canvas grouping
  // ... 30+ additional Canvas-specific properties
}
```

**Reason for Legacy Classification:**
- Defines absolute positioning (x, y)
- Includes Canvas-specific transformations (rotation, zIndex)
- Fixed dimensions (width, height)
- Canvas grouping concepts (groupId)

**Impact:** HIGH  
**Recommended Fix:** 
1. Create new `ProseMirrorNodeAttrs` interface based on ProseMirror schema
2. Replace all `DesignerElement` references with ProseMirror node types
3. Remove coordinate-based properties entirely

**Migration Risk:** HIGH - This type is referenced in 15+ files  
**Priority:** P0 - CRITICAL  
**Status:** ⚠️ ACTIVE LEGACY CODE

---

### 1.2 Legacy Element Conversion Functions

**File:** `eddp_frontend/src/features/templates/components/TemplateForm.tsx`  
**Lines:** 413-500

**Current Implementation:**
```typescript
// ❌ LEGACY: Extracts Canvas elements from content
const extractLegacyElementsFromContentJson = (
  contentJson?: string
): DesignerElement[] => {
  // Parses stored content as DesignerElement array
  return parsed as DesignerElement[];
}

// ❌ LEGACY: Converts Canvas elements to HTML
const legacyElementsToHtml = (
  elements: DesignerElement[]
): string => {
  const sorted = [...elements].sort(
    (a, b) => (a.page - b.page) || (a.y - b.y) // Position-based sorting
  );
  // Generates HTML from coordinates
}

// ❌ LEGACY: Converts HTML back to Canvas elements
const htmlToLegacyElements = (
  html: string,
  pageSize: PageSize,
  orientation: Orientation,
  referenceElements: DesignerElement[] = [],
): DesignerElement[] => {
  // Assigns x, y coordinates to HTML elements
  // Creates DesignerElement objects with positions
}
```

**Reason for Legacy Classification:**
- Actively converts between Canvas `DesignerElement[]` and HTML
- Uses positional sorting (`a.y - b.y`)
- Generates coordinate-based element arrays
- Named "legacy" by developers but still in production use

**Impact:** CRITICAL  
**Recommended Fix:**
1. Delete all three functions
2. Replace with `prosemirrorToHtml()` utility using ProseMirror serializer
3. Store only ProseMirror JSON, generate HTML on-demand

**Migration Risk:** HIGH - Used in save/load workflows  
**Priority:** P0 - CRITICAL  
**Status:** ⚠️ ACTIVE IN PRODUCTION

---

### 1.3 Page Dimension Constants

**File:** `eddp_frontend/src/features/templates/components/TemplateForm.tsx`  
**Lines:** 93-97

**Current Implementation:**
```typescript
// ⚠️ LEGACY REMNANT: Canvas page sizing
const PAGE_DIMENSIONS: Record<PageSize, { width: number; height: number }> = {
  A4: { width: 794, height: 1123 },
  A3: { width: 1123, height: 1587 },
  LETTER: { width: 816, height: 1056 },
  LEGAL: { width: 816, height: 1344 },
};
```

**Reason for Legacy Classification:**
- Used to calculate absolute pixel positions on Canvas
- Still referenced by `htmlToLegacyElements` to position elements
- Page-flow editors (Tiptap/ProseMirror) don't need pixel dimensions

**Impact:** MEDIUM  
**Recommended Fix:**
1. Keep for PDF rendering (which DOES need dimensions)
2. Remove all references from element positioning logic
3. Use CSS page size (@page) for rendering instead

**Migration Risk:** LOW - Safe to refactor  
**Priority:** P2  
**Status:** ⚠️ LEGACY REMNANT

---

### 1.4 Selection Context - Canvas Element References

**File:** `eddp_frontend/src/features/templates/contexts/SelectionContext.tsx`  
**Lines:** 1-80

**Current Implementation:**
```typescript
interface SelectionContextValue {
  selectedElementIds: string[];
  selectedElements: DesignerElement[]; // ❌ References Canvas type
  primaryElement: DesignerElement | null; // ❌ Canvas element
  selectionType: SelectionType;
  // ...
}

export function SelectionProvider({
  elements, // ❌ DesignerElement[] array
  selectedIds,
  // ...
}: SelectionProviderProps) {
  const selectedElements = useMemo(
    () => elements.filter((el) => selectedIds.includes(el.id)),
    [elements, selectedIds]
  );
  // ...
}
```

**Reason for Legacy Classification:**
- Expects `DesignerElement[]` array (Canvas model)
- ProseMirror uses node tree, not flat element arrays
- Selection should work with ProseMirror positions/ranges, not element IDs

**Impact:** HIGH  
**Recommended Fix:**
1. Replace with ProseMirror Selection API
2. Use `editor.state.selection` instead of element arrays
3. Remove `DesignerElement` dependency

**Migration Risk:** HIGH - Core selection system  
**Priority:** P0 - CRITICAL  
**Status:** ⚠️ BLOCKING TIPTAP INTEGRATION

---

### 1.5 Track Changes Extension - Position-Based Decorations

**File:** `eddp_frontend/src/features/templates/components/EnterpriseTrackChangesExtension.ts`  
**Lines:** 177-288

**Current Implementation:**
```typescript
const buildMatchLocations = (
  doc: ProseMirrorNode,
  changes: ElementChange[]
): Record<string, MatchLocation> => {
  // Maps ProseMirror positions correctly ✅
}

const buildDecorations = (
  doc: ProseMirrorNode,
  changes: ElementChange[]
): DecorationSet => {
  // Creates inline decorations ✅
}
```

**Classification:** ✅ CORRECT IMPLEMENTATION  
This is **NOT legacy** - it properly uses ProseMirror's decoration system.

**Status:** ✅ COMPLIANT WITH NEW ARCHITECTURE

---

## 2. BACKEND AUDIT - Django Models & APIs

### 2.1 Template Model - Legacy Content Storage

**File:** `eddp_backend/apps/templates/models.py`  
**Lines:** 45

**Current Implementation:**
```python
class Template(BaseModel):
    # ...
    content_json = models.TextField(
        blank=True, 
        null=True
    )  # ❌ COMMENT: "Stores serialized designer elements"
```

**Reason for Legacy Classification:**
- Comment says "designer elements" (Canvas terminology)
- Field name is ambiguous (could be Canvas OR ProseMirror)
- Database field should be renamed to clarify it NOW stores ProseMirror

**Impact:** MEDIUM  
**Recommended Fix:**
1. Rename to `prosemirror_json` (with migration)
2. Update comment: "Stores ProseMirror document JSON"
3. Add validation to ensure `{prosemirror_json: {...}}` structure

**Migration Risk:** MEDIUM - Database migration required  
**Priority:** P1  
**Status:** ⚠️ MISLEADING DOCUMENTATION

---

### 2.2 Word Document Parser - Generates Canvas Elements

**File:** `eddp_backend/apps/templates/parsers.py`  
**Lines:** 1-180

**Current Implementation:**
```python
class WordDocumentParser:
    """Parse Word documents and convert to template canvas JSON"""
    
    def __init__(self):
        self.elements = []          # ❌ LEGACY: Canvas element array
        self.y_position = 104       # ❌ LEGACY: Absolute Y coordinate
        self.x_position = 24        # ❌ LEGACY: Absolute X coordinate
    
    def parse(self, file_path_or_stream) -> List[Dict[str, Any]]:
        """Returns: List of template elements in JSON format"""
        # ...
        return self.elements  # ❌ Returns Canvas elements, not ProseMirror
    
    def _parse_paragraph(self, paragraph) -> None:
        element = {
            "id": str(uuid.uuid4()),
            "type": "heading" if is_heading else "paragraph",
            "x": self.x_position,      # ❌ LEGACY: Canvas X
            "y": self.y_position,      # ❌ LEGACY: Canvas Y
            "width": 760,              # ❌ LEGACY: Fixed width
            "height": height,          # ❌ LEGACY: Fixed height
            "zIndex": len(self.elements) + 1,  # ❌ LEGACY: Z-index
            # ...
        }
        self.elements.append(element)
        self.y_position += height + 10  # ❌ LEGACY: Position tracking
```

**Reason for Legacy Classification:**
- Docstring mentions "canvas JSON"
- Generates `DesignerElement` objects with x/y coordinates
- Tracks vertical position manually (`y_position`)
- Assigns z-index for layering

**Impact:** CRITICAL  
**Recommended Fix:**
1. Rewrite parser to generate ProseMirror JSON directly
2. Use Mammoth.js (which outputs HTML) → convert to ProseMirror
3. Delete coordinate calculation logic entirely

**Migration Risk:** HIGH - DOCX import will break  
**Priority:** P0 - CRITICAL  
**Status:** ⚠️ ACTIVE LEGACY - BREAKS NEW ARCHITECTURE

---

### 2.3 Diff Utils - Position-Based Change Detection

**File:** `eddp_backend/apps/templates/diff_utils.py`  
**Lines:** 300-350

**Current Implementation:**
```python
class TemplateElementDiffer:
    @classmethod
    def _infer_semantic_type(cls, old_node, new_node):
        # ...
        # ❌ LEGACY: Detects coordinate changes
        if old_attrs.get("x") != new_attrs.get("x") or \
           old_attrs.get("y") != new_attrs.get("y"):
            return "POSITION_CHANGED"
        return "UNKNOWN_CHANGE"
    
    @classmethod
    def _build_structured_change(cls, node_id, coarse_change_type, 
                                  old_node, new_node, index):
        return {
            "changeId": f"chg-{node_id}-{index}",
            # ❌ LEGACY: Tracks old/new positions
            "oldPosition": {
                "x": old_attrs.get("x"),
                "y": old_attrs.get("y"),
                "path": old_node.get("path") if old_node else None,
            },
            "newPosition": {
                "x": new_attrs.get("x"),
                "y": new_attrs.get("y"),
                "path": new_node.get("path") if new_node else None,
            },
            # ...
        }
```

**Reason for Legacy Classification:**
- Detects `POSITION_CHANGED` by comparing x/y coordinates
- Stores `oldPosition` and `newPosition` with x/y values
- ProseMirror documents don't have positions - nodes have document order

**Impact:** HIGH  
**Recommended Fix:**
1. Remove `POSITION_CHANGED` detection (meaningless for document-flow editors)
2. Remove `oldPosition.x/y` and `newPosition.x/y` fields
3. Keep `path` (ProseMirror document path is valid)
4. Focus on semantic changes: text, marks, attributes, node type

**Migration Risk:** MEDIUM - Review workflows depend on this  
**Priority:** P1  
**Status:** ⚠️ CONCEPTUALLY INCORRECT FOR PROSEMIRROR

---

### 2.4 Template Service - Content Canonicalization

**File:** `eddp_backend/apps/templates/services.py`  
**Lines:** 89-115

**Current Implementation:**
```python
class TemplateService:
    @staticmethod
    def _canonicalize_content_json(content: Any) -> str:
        """Persist template content as canonical {prosemirror_json: doc} JSON string."""
        # ✅ CORRECT: Normalizes to ProseMirror format
        # Handles legacy formats and converts them
        
        # Extracts ProseMirror doc from various formats:
        # - Direct doc object
        # - {prosemirror_json: doc}
        # - {pm_json: doc}
        # - {tiptap_json: doc}
        # - {doc: doc}
        
        return json.dumps({'prosemirror_json': pm_doc})
```

**Classification:** ✅ CORRECT MIGRATION LOGIC  
This function is doing the RIGHT thing - it's a **compatibility layer** that normalizes legacy formats to the new canonical structure.

**Impact:** POSITIVE  
**Recommended Fix:** Keep this function until all legacy data is migrated  
**Migration Risk:** LOW  
**Priority:** N/A - Part of migration strategy  
**Status:** ✅ COMPLIANT - MIGRATION HELPER

---

### 2.5 Template Service - Review Change Detection

**File:** `eddp_backend/apps/templates/services.py`  
**Lines:** 579-755

**Current Implementation:**
```python
# ⚠️ MIXED: Uses both legacy position tracking AND ProseMirror logic
if semantic_type in {'POSITION_CHANGED', 'IMAGE_MOVED'}:
    if semantic.get('oldPosition') == semantic.get('newPosition'):
        continue  # Skip if no actual movement
    
# Builds change record with position info
'old_position': semantic.get('oldPosition') if semantic else None,
'new_position': semantic.get('newPosition') if semantic else None,
```

**Reason for Classification:**
- References `POSITION_CHANGED` semantic type (Canvas concept)
- Reads `oldPosition` / `newPosition` from diff results
- This is coming from the `diff_utils.py` legacy logic

**Impact:** MEDIUM  
**Recommended Fix:**
1. Remove position-based filtering once `diff_utils.py` is fixed
2. Remove `old_position` / `new_position` from change records
3. Focus on node path and semantic meaning

**Migration Risk:** LOW - Dependent on diff_utils fix  
**Priority:** P2  
**Status:** ⚠️ DEPENDS ON DIFF_UTILS REFACTOR

---

## 3. DATABASE AUDIT - Schema Fields

### 3.1 Template.content_json Field

**File:** `eddp_backend/apps/templates/models.py`  
**Line:** 45

**Current Schema:**
```python
content_json = models.TextField(blank=True, null=True)
```

**Issues:**
1. Field name doesn't indicate it stores ProseMirror
2. Database allows NULL (should default to empty doc)
3. No validation constraint

**Recommended Migration:**
```python
# Option A: Rename field (requires migration)
prosemirror_json = models.TextField(
    default='{"prosemirror_json": {"type": "doc", "content": []}}',
    help_text="ProseMirror document in canonical format"
)

# Option B: Keep field name, update docs (no migration)
content_json = models.TextField(
    default='{"prosemirror_json": {"type": "doc", "content": []}}',
    help_text="ProseMirror document JSON (canonical format)"
)
```

**Migration Risk:** LOW (Option B) / MEDIUM (Option A)  
**Priority:** P1  
**Status:** ⚠️ NEEDS DOCUMENTATION UPDATE

---

### 3.2 TemplateVersion.template_json Field

Similar issues as Template.content_json - same recommendations apply.

---

### 3.3 Migration History

**Files:** 
- `eddp_backend/apps/templates/migrations/0002_template_content_json.py`
- `eddp_backend/apps/templates/migrations/0003_template_approved_at_template_approved_by_and_more.py`

**Observation:** 
- No migration to convert legacy Canvas elements to ProseMirror
- Migration #0002 added `content_json` field (name suggests legacy)
- No data transformation migrations exist

**Recommended Fix:**
1. Create data migration: `0004_convert_canvas_to_prosemirror.py`
2. Scan all templates with Canvas element arrays
3. Convert to ProseMirror JSON using server-side logic
4. Mark converted templates for verification

**Migration Risk:** HIGH - Data transformation  
**Priority:** P0 - REQUIRED BEFORE REMOVING LEGACY CODE  
**Status:** ⚠️ MISSING DATA MIGRATION

---

## 4. API AUDIT

### 4.1 Template Import API

**File:** `eddp_backend/apps/templates/views.py`  
**Lines:** 149-152

**Current Implementation:**
```python
@action(detail=False, methods=["POST"])
def import_word(self, request) -> Response:
    parser = WordDocumentParser()  # ❌ Returns Canvas elements
    elements = parser.parse(file)
    return Response(
        data={"elements": elements},  # ❌ Returns element array, not ProseMirror
        status=status.HTTP_200_OK,
    )
```

**Impact:** CRITICAL  
**Recommended Fix:**
1. Parse DOCX with Mammoth (outputs HTML)
2. Convert HTML → ProseMirror JSON on backend
3. Return `{"prosemirror_json": {...}}`

**Priority:** P0  
**Status:** ⚠️ API RETURNS LEGACY FORMAT

---

### 4.2 Template Update API

**File:** `eddp_backend/apps/templates/views.py`  
**Lines:** 178-186

**Current Implementation:**
```python
@action(detail=True, methods=["PUT"])
def update_draft_content(self, request, pk=None) -> Response:
    """Update draft version content_json and regenerate diff changes."""
    new_content_json = request.data.get('content_json')
    # ✅ Uses canonicalization function
    response = service.update_draft_version(pk, version_number, user, new_content_json)
```

**Classification:** ✅ CORRECT  
Accepts any format, canonicalizes to ProseMirror via service layer.

**Status:** ✅ COMPLIANT

---

## 5. RENDERING AUDIT

### 5.1 Frontend HTML Generation

**Current State:**
- ✅ Tiptap editor generates HTML from ProseMirror automatically
- ⚠️ Legacy `legacyElementsToHtml()` still exists for backward compatibility
- ❌ Some components may still call legacy converters

**Recommended Fix:**
1. Audit all render paths
2. Ensure all use `editor.getHTML()` (Tiptap's built-in)
3. Delete `legacyElementsToHtml()` function

**Priority:** P1  
**Status:** ⚠️ MIXED STATE

---

### 5.2 PDF Rendering

**Status:** NOT AUDITED  
**Action Required:** Verify PDF generation uses ProseMirror → HTML → PDF pipeline

---

### 5.3 Word Export

**Status:** NOT AUDITED  
**Action Required:** Verify DOCX generation uses ProseMirror → HTML → DOCX pipeline

---

## 6. VARIABLE ENGINE AUDIT

### 6.1 Variable Implementation

**Observation:** Variables appear as `{{variable_name}}` tokens in text.

**Current State:**
- ✅ Track changes extension recognizes variable tokens
- ⚠️ Variables stored as text content (not custom nodes?)
- ❌ No Custom ProseMirror Node for variables

**Recommended Architecture:**
```typescript
// Custom Tiptap node
const VariableNode = Node.create({
  name: 'variable',
  group: 'inline',
  inline: true,
  atom: true,
  
  addAttributes() {
    return {
      variableKey: { default: null },
      variableLabel: { default: null },
    }
  },
  
  parseHTML() {
    return [{ tag: 'span[data-variable]' }]
  },
  
  renderHTML({ node, HTMLAttributes }) {
    return ['span', mergeAttributes(HTMLAttributes, {
      'data-variable': node.attrs.variableKey,
      class: 'variable-chip'
    }), `{{${node.attrs.variableKey}}}`]
  },
})
```

**Impact:** MEDIUM  
**Priority:** P2  
**Status:** ⚠️ NEEDS CUSTOM NODE IMPLEMENTATION

---

## 7. REVIEW ENGINE AUDIT

### 7.1 Change Detection Logic

**Current State:**
- ✅ Uses ProseMirror node comparison in `diff_utils.py`
- ❌ Still tracks `POSITION_CHANGED` (Canvas concept)
- ⚠️ Marks stored as `oldPosition`/`newPosition`

**Recommended Fix:**
1. Remove position-based change types
2. Focus on:
   - Node type changes
   - Attribute changes  
   - Mark changes (bold, italic, etc.)
   - Text content changes
   - Structure changes (nesting, order)

**Priority:** P1  
**Status:** ⚠️ PARTIALLY CORRECT

---

### 7.2 Review UI Components

**Status:** NOT AUDITED  
**Action Required:** Verify review interface works with ProseMirror changes, not Canvas positions

---

## 8. APPROVAL WORKFLOW AUDIT

**Status:** NOT FULLY AUDITED

**Observation:** Uses semantic change types from diff_utils.py, so approval workflow inherits the same position-based issues.

**Priority:** P2  
**Status:** ⚠️ DEPENDS ON DIFF_UTILS REFACTOR

---

## 9. RUNTIME GENERATION AUDIT

**Status:** NOT AUDITED  
**Action Required:** Verify document generation uses ProseMirror → variable resolution → HTML → PDF

---

## 10. WORD IMPORT/EXPORT AUDIT

### 10.1 Import (DOCX → Platform)

**Current State:** ❌ LEGACY  
- `WordDocumentParser` generates Canvas elements
- See Section 2.2

### 10.2 Export (Platform → DOCX)

**Status:** NOT AUDITED  
**Action Required:** Verify export uses ProseMirror JSON, not Canvas elements

---

## 11. SEARCH KEYWORD FINDINGS

### Keywords Found:
- ✅ `canvas` - 3 matches (comments only, not active)
- ❌ `elements[]` / `DesignerElement` - 100+ matches (ACTIVE)
- ❌ `x`, `y`, `width`, `height`, `rotation`, `zIndex` - 100+ matches (ACTIVE)
- ❌ `position`, `coordinate` - 50+ matches (ACTIVE in diff_utils)
- ✅ `DeepDiff` - Used correctly for semantic comparison
- ✅ `prosemirror`, `tiptap`, `@tiptap` - Present (new architecture)

---

## 12. DEPENDENCY SUMMARY

| Dependency Type | Status | Priority | Files Affected |
|----------------|--------|----------|----------------|
| `DesignerElement` Type | ❌ Active | P0 | 15+ frontend files |
| Legacy Conversion Functions | ❌ Active | P0 | TemplateForm.tsx (3 functions) |
| Canvas Element Arrays | ❌ Active | P0 | SelectionContext, parsers.py |
| Position Change Detection | ❌ Active | P1 | diff_utils.py, services.py |
| Word Parser Canvas Output | ❌ Active | P0 | parsers.py |
| Database Field Names | ⚠️ Ambiguous | P1 | models.py |
| API Response Formats | ❌ Legacy | P0 | import_word endpoint |

---

## 13. MIGRATION CHECKLIST

### Phase 1: Stop the Bleeding (P0 - Critical)
- [ ] **Delete `extractLegacyElementsFromContentJson()`** - No longer needed
- [ ] **Delete `legacyElementsToHtml()`** - Use Tiptap's `editor.getHTML()`
- [ ] **Delete `htmlToLegacyElements()`** - Should never create Canvas elements
- [ ] **Rewrite `WordDocumentParser`** - Generate ProseMirror JSON, not Canvas elements
- [ ] **Fix `import_word` API** - Return ProseMirror JSON
- [ ] **Create data migration** - Convert any remaining Canvas content to ProseMirror

### Phase 2: Type System Cleanup (P0 - Critical)
- [ ] **Remove `DesignerElement` interface** - Replace with ProseMirror types
- [ ] **Update `SelectionContext`** - Use ProseMirror Selection API
- [ ] **Remove x/y/width/height properties** - Not applicable to document-flow editors

### Phase 3: Diff & Review (P1 - High)
- [ ] **Remove `POSITION_CHANGED` detection** - Meaningless for ProseMirror
- [ ] **Remove `oldPosition`/`newPosition` fields** - Keep `path` only
- [ ] **Update review UI** - Show semantic changes, not position changes

### Phase 4: Documentation & Cleanup (P1 - High)
- [ ] **Rename `content_json` field** - Consider `prosemirror_json`
- [ ] **Update all comments** - Remove "designer elements", "canvas" references
- [ ] **Add validation** - Ensure all content is canonical ProseMirror format
- [ ] **Update API documentation** - All endpoints use ProseMirror

### Phase 5: Advanced Features (P2 - Medium)
- [ ] **Implement Variable Custom Node** - Replace text tokens with nodes
- [ ] **Verify PDF rendering** - Uses ProseMirror → HTML → PDF
- [ ] **Verify Word export** - Uses ProseMirror → HTML → DOCX
- [ ] **Remove PAGE_DIMENSIONS** - Only needed for PDF, not editor

### Phase 6: Final Validation (P2 - Medium)
- [ ] **Audit all imports** - No Canvas library references
- [ ] **Search codebase** - Zero matches for "DesignerElement"
- [ ] **Test all workflows** - Import, edit, review, approve, generate, export
- [ ] **Verify database** - All templates use canonical ProseMirror format

---

## 14. RISKS & CONSIDERATIONS

### High-Risk Areas:
1. **Data Loss** - Converting Canvas elements to ProseMirror might lose layout info
   - Mitigation: Keep backup of original content_json during migration
2. **Breaking Changes** - Removing DesignerElement will break many components
   - Mitigation: Comprehensive testing, staged rollout
3. **Review Workflow** - Existing change approvals reference positions
   - Mitigation: Mark old changes as "legacy format", new reviews use semantic model

### Low-Risk Areas:
1. **Tiptap Editor** - Already working correctly
2. **Track Changes Extension** - Uses ProseMirror properly
3. **Canonicalization Service** - Doing the right thing

---

## 15. SUCCESS CRITERIA

✅ The migration is **COMPLETE** when:

1. **Zero `DesignerElement` references** in codebase (except historical documentation)
2. **All content stored as `{prosemirror_json: {...}}`** in database
3. **Word import outputs ProseMirror JSON** (not Canvas elements)
4. **Diff engine compares ProseMirror nodes** (not positions)
5. **Review system shows semantic changes** (not coordinate changes)
6. **No coordinate-based logic** (x, y, width, height, rotation, zIndex)
7. **All rendering starts from ProseMirror** (HTML, PDF, DOCX generated from PM)
8. **Variables implemented as custom nodes** (not text tokens)

---

## 16. ESTIMATED EFFORT

| Phase | Effort | Risk |
|-------|--------|------|
| Phase 1: Stop the Bleeding | 2-3 days | HIGH |
| Phase 2: Type System Cleanup | 3-5 days | HIGH |
| Phase 3: Diff & Review | 2-3 days | MEDIUM |
| Phase 4: Documentation | 1-2 days | LOW |
| Phase 5: Advanced Features | 3-4 days | MEDIUM |
| Phase 6: Final Validation | 2-3 days | LOW |
| **TOTAL** | **13-20 days** | - |

---

## 17. CONCLUSION

The Enterprise Dynamic Document Platform is in a **transitional state** between two fundamentally incompatible architectures:

1. **Old:** Canvas/Figma editor with absolute positioning
2. **New:** Tiptap/ProseMirror with document-flow editing

**The new architecture is functional but coexists with significant legacy code.**

**Critical Path:**
1. Delete legacy conversion functions (immediate)
2. Fix Word import to generate ProseMirror (urgent)
3. Remove position-based diff logic (high priority)
4. Clean up type system (high priority)
5. Data migration for existing templates (required before production)

**The migration can be completed in 2-4 weeks with focused effort.**

---

**Report Prepared By:** GitHub Copilot Architectural Audit  
**Review Status:** Ready for Engineering Review  
**Next Steps:** Present findings to engineering team, prioritize migration tasks

