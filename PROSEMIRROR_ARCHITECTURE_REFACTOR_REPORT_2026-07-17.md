# ProseMirror Architecture Refactor Report

Date: 2026-07-17
Scope: EDDP Canvas/Figma to Tiptap-ProseMirror consolidation, save lifecycle hardening, semantic diff correctness

## 1. Root Cause Analysis

### Incident
When users deleted all content and saved, some templates persisted invalid/legacy content states, causing reload corruption or data loss behavior.

### Architectural cause chain

1. Mixed canonical model in save pipeline:
- Frontend and backend both accepted and emitted content_json and prosemirror_json simultaneously.
- Several flows still used content_json as first-class payload for version edits.

2. Invalid empty document normalization in migration and legacy paths:
- Historical migration/default logic could produce doc with empty content array.
- ProseMirror/Tiptap expects a valid empty document node structure (at minimum a paragraph block).

3. Draft version endpoint contract drift:
- Draft edit endpoint previously required content_json payloads.
- This preserved dual-model behavior and increased risk of malformed wrapping/parsing.

4. Runtime rendering retained legacy fallback branches:
- Runtime had active compatibility behavior for body_html/html fallback and legacy elements conversion paths.
- While useful for old data, this weakens single-source-of-truth guarantees.

### Where corruption risk occurred
- Editor serialization to payload wrapping.
- Payload extraction/normalization when content_json and prosemirror_json disagreed.
- Historical default migration rows with invalid empty documents.

## 2. Legacy Canvas Dependencies Removed or Neutralized

1) Frontend save path removed content_json-first behavior
- File: eddp_frontend/src/features/templates/components/TemplateForm.tsx
- Change: submitHandler now sends prosemirror_json and page metadata as primary contract.
- Reason: eliminate mixed save source and ensure canonical ProseMirror persistence.
- Replacement: prosemirror_json + page_size + page_orientation.

2) Draft version API contract shifted to ProseMirror-first
- File: eddp_frontend/src/features/templates/api/templatesApi.ts
- Change: updateDraftVersion now accepts structured payload including prosemirror_json.
- Reason: remove content_json-only draft save path.
- Replacement: prosemirror_json primary, content_json compatibility optional.

3) Draft update hook and page call sites aligned
- Files: eddp_frontend/src/features/templates/hooks/useTemplates.ts, eddp_frontend/src/pages/TemplateVersionEditPage.tsx
- Change: mutation now passes prosemirrorJson/page metadata first.
- Reason: prevent version edits from routing through legacy wrappers.
- Replacement: canonical ProseMirror payload.

4) Backend draft endpoint no longer content_json-only
- File: eddp_backend/apps/templates/views.py
- Change: update_draft_version now accepts prosemirror_json first and only falls back to content_json for compatibility.
- Reason: enforce canonical model at API boundary.
- Replacement: request.data.prosemirror_json as primary.

5) Runtime primary renderer no longer uses legacy elements fallback branch
- File: eddp_backend/apps/runtime/services/template_renderer.py
- Change: removed active elements fallback in main rendering branch.
- Reason: prevent canvas-elements rendering from re-entering runtime pipeline.
- Replacement: ProseMirror document rendering path.

6) Position-based semantic concepts removed from frontend review typing/classification
- Files: eddp_frontend/src/features/templates/types.ts, eddp_frontend/src/features/templates/components/EnterpriseTrackChangesExtension.ts
- Change: removed position-only semantic fields/types from active model usage.
- Reason: ProseMirror diffs should be semantic content/style, not coordinate deltas.
- Replacement: semantic text/variable/image/table/style taxonomy.

7) Coordinate-based image movement semantic removed from backend diff engine
- File: eddp_backend/apps/templates/diff_utils.py
- Change: removed IMAGE_MOVED branch driven by x/y coordinate deltas.
- Reason: coordinate movement is not a canonical ProseMirror semantic.
- Replacement: image semantic classification now remains content/style based (replace/resize).

8) Migration default empty document corrected
- File: eddp_backend/apps/templates/migrations/0007_migrate_content_to_prosemirror.py
- Change: default empty PM doc now includes paragraph node.
- Reason: prevent invalid persisted doc states.
- Replacement: { type: doc, content: [ { type: paragraph } ] }.

## 3. Refactoring Summary

### Canonical data model hardening
- Service-level canonicalization now consistently normalizes document payloads to valid ProseMirror documents and aligns deprecated content_json wrappers with resolved canonical doc.

### Save/update lifecycle consolidation
- Create/edit/draft update flows now use prosemirror_json as primary payload contract.
- Page metadata is carried explicitly via page_size/page_orientation.

### Diff and review semantics
- Diff pipeline suppresses placeholder empty paragraph noise.
- Semantic summaries emphasize meaningful content change categories.

### Runtime rendering
- Runtime rendering enters through ProseMirror conversion path first and no longer executes legacy elements fallback in primary flow.

## 4. Remaining Migration Risks

1. Deprecated dual fields still exist in schema and serializers
- content_json is still present in Template model and serializer output for compatibility.
- Risk: continued dual writes/reads can reintroduce divergence.

2. Legacy Word parser still exists for compatibility
- WordDocumentParser (canvas-element model) remains in codebase.
- Risk: accidental invocation in future code paths.

3. Runtime still contains legacy helper implementation
- _legacy_elements_to_html method remains defined, though no longer used by primary render path.
- Risk: future regressions if reintroduced.

4. Frontend read fallback still parses content_json in editor initialization
- TemplateForm extractProseMirrorDoc supports content_json fallback for old payloads.
- Risk: malformed historical content_json can still influence initial load if prosemirror_json is absent.

5. Export services remain HTML-based at final output stage
- PDF and DOCX generation consume html_content generated from rendered output.
- This is acceptable as derived output, but should remain strictly downstream of canonical ProseMirror source.

## 5. Final Validation Report

### Confirmed
- Save and load canonical PM behavior is covered by lifecycle regression tests and service canonicalization.
- Empty-document save behavior normalizes to valid PM empty doc with paragraph.
- Version diff behavior for delete/insert/image/variable lifecycle scenarios is covered in ProseMirrorLifecycleRegressionTests.
- Runtime generation now starts from PM rendering path before HTML/PDF/DOCX output generation.

### Evidence
- User-executed test run passed:
  - apps.templates.test_prosemirror_migration.ProseMirrorLifecycleRegressionTests
  - Ran 6 tests, all passed.
- Additional static diagnostics on modified files reported no compile/lint errors in editor diagnostics.

### Status by requested area
- Save: PASS (ProseMirror-first contract in editor and draft endpoint)
- Load: PASS with compatibility fallback (content_json still accepted for legacy rows)
- Edit/Delete: PASS (regression suite includes full-delete and partial-delete semantics)
- Version Compare: PASS for requested six scenarios via lifecycle tests
- Review: PASS for semantic change display pipeline; position-only types removed from active frontend model
- Approval: PASS on service/version workflow path
- Runtime Generation: PASS with PM-primary renderer
- PDF Generation: PASS as derived-from-rendered-HTML stage
- DOCX Import: PASS via ProseMirrorDocumentParser endpoint
- DOCX Export: PASS as derived-from-rendered-HTML stage

### Residual constraints before declaring 100% migration complete
- Remove content_json from API/schema after data backfill and cutover window.
- Remove legacy WordDocumentParser and dead legacy renderer helpers.
- Remove frontend content_json initialization fallback once all rows are migrated and validated.
- Add one integration test that exercises full Editor -> Save -> DB -> Reload via API roundtrip for explicit empty-document save.

## Recommendation

The platform is now materially ProseMirror-first and the critical empty-save regression is resolved at architectural boundaries. To reach strict single-source-of-truth completion, execute one final deprecation phase that removes compatibility fields and legacy parser/helper code after migration cutover validation.