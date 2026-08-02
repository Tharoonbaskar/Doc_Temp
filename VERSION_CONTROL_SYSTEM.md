# Template Version Control System

## Overview

A comprehensive version control system has been implemented for template management with visual diff tracking and granular change approval similar to VS Code's merge conflict resolution.

## Key Features

### 1. Automatic Version Creation
- When an **APPROVED** template is edited, the system automatically creates a new **DRAFT** version
- Version numbers increment automatically (v1.0 → v2.0 → v3.0...)
- Each draft version maintains a reference to its base approved version

### 2. Visual Diff Tracking
Element-level changes are color-coded:
- **Green**: Added elements
- **Amber/Orange**: Modified elements  
- **Red**: Deleted elements

### 3. Granular Approval
Reviewers can approve/reject/revert individual changes:
- **Approve**: Accept the change
- **Reject**: Decline the change
- **Revert**: Restore to original value

Similar to VS Code's conflict resolution interface.

## Backend Implementation

### Models

#### TemplateVersion (Updated)
New fields added:
- `version_status`: DRAFT | APPROVED | REJECTED
- `base_version`: Reference to the approved version this draft is based on
- `diff_data`: JSON field storing the calculated differences
- `approved_by`: User who approved this version
- `approved_at`: Timestamp of approval

#### TemplateElementChange (New)
Tracks individual element-level changes:
- `element_id`: Unique identifier of the template element
- `change_type`: ADDED | MODIFIED | DELETED
- `old_value`: Original element data (null for ADDED)
- `new_value`: New element data (null for DELETED)
- `approval_status`: PENDING | APPROVED | REJECTED | REVERTED
- `reviewed_by`: User who reviewed this change
- `review_comment`: Optional comment from reviewer

### Services

#### TemplateService.create_draft_version_from_approved()
- Triggered automatically when updating an approved template's content
- Calculates diff between base version and new content using `deepdiff`
- Creates TemplateVersion record with status=DRAFT
- Generates TemplateElementChange records for each detected change

#### TemplateService.review_element_change()
- Allows reviewers to approve/reject individual changes
- Updates the approval_status of a specific TemplateElementChange

#### TemplateService.approve_draft_version()
- Validates all changes have been reviewed
- Merges approved changes into the base version
- Marks the version as APPROVED
- Updates the main template content with merged changes

### API Endpoints

```
GET    /api/templates/{id}/versions/{version_number}/changes/
POST   /api/templates/{id}/versions/{version_number}/approve/
POST   /api/templates/changes/{change_id}/review/
```

### Diff Calculation (`diff_utils.py`)

Uses the `deepdiff` library to:
1. Compare element arrays by unique IDs
2. Detect additions, modifications, and deletions
3. Generate structured diff data with change details
4. Produce human-readable change summaries
5. Merge approved changes back into the base version

## Frontend Implementation

### Components

#### ElementDiffView
Displays a single element change with:
- Color-coded change type indicator
- Side-by-side comparison (old vs new)
- Status chip (Pending/Approved/Rejected)
- Action buttons (Approve/Reject/Revert)

#### TemplateVersionReviewPage
Complete review interface showing:
- Version summary card with statistics
- Progress indicators (approved/rejected/pending counts)
- List of all element changes
- Final approval button (enabled when all changes reviewed)

### API Integration

New React Query hooks:
- `useVersionChanges()` - Fetch version changes
- `useReviewElementChange()` - Review individual change
- `useApproveDraftVersion()` - Approve entire version

### Routing

New route added:
```
/templates/:id/versions/:versionNumber/review
```

## Workflow

### For Template Editors

1. **Edit Approved Template**
   - Navigate to an APPROVED template
   - Click Edit
   - Make changes to the template content
   - Save changes
   - **System automatically creates v2.0 DRAFT** with element-level diff

2. **View Draft Status**
   - Template status remains APPROVED (master)
   - Draft version v2.0 created in background
   - Changes tracked for reviewer

### For Approvers

1. **Review Changes**
   - Navigate to Template Approvals section
   - See templates with draft versions pending review
   - Click "Review Version" to see element-level changes

2. **Granular Approval**
   - See each element change color-coded:
     - Green box = Added content
     - Orange box = Modified content (old vs new comparison)
     - Red box = Deleted content
   
3. **Review Actions (per change)**
   - **Approve**: Accept this specific change
   - **Reject**: Decline this specific change
   - **Revert**: Restore to original value
   - Add optional comment

4. **Final Approval**
   - Once all changes reviewed, click "Approve Version"
   - System merges only APPROVED changes
   - Version becomes v2.0 APPROVED
   - Template content updated with merged changes

## Database Changes

### New Tables
- `TemplateElementChange` - Tracks individual element changes

### Modified Tables
- `TemplateVersion`:
  - Added `version_status` field
  - Added `base_version_id` foreign key
  - Added `diff_data` JSON field
  - Added `approved_by` and `approved_at` fields

### Migrations Required
Run:
```bash
cd eddp_backend
python manage.py makemigrations
python manage.py migrate
```

## Dependencies

### Backend (requirements.txt)
```
deepdiff==8.0.1
```

Install with:
```bash
cd eddp_backend
venv\Scripts\pip.exe install deepdiff==8.0.1
```

### Frontend
No additional dependencies required - uses existing Material-UI components.

## Testing Checklist

- [ ] Install deepdiff package
- [ ] Run database migrations
- [ ] Create and approve a template (v1.0)
- [ ] Edit the approved template
- [ ] Verify v2.0 DRAFT created automatically
- [ ] Navigate to version review page
- [ ] See element changes with color coding
- [ ] Approve some changes, reject others
- [ ] Verify final approval merges only approved changes
- [ ] Check version history shows both v1.0 and v2.0

## Future Enhancements

1. **Version Comparison View**: Side-by-side comparison of any two versions
2. **Rollback**: Ability to rollback to any previous approved version
3. **Merge Conflicts**: Handle concurrent edits from multiple users
4. **Batch Operations**: Approve/reject multiple changes at once
5. **Email Notifications**: Notify approvers when new versions pending review
6. **Audit Trail**: Complete history of who approved/rejected each change
7. **Comments Thread**: Conversation thread on each element change

## Architecture Decisions

1. **Why element-level tracking?**
   - Allows granular control over what gets approved
   - Prevents "all or nothing" approval scenarios
   - Better auditability

2. **Why automatic version creation?**
   - Prevents accidental overwrites of approved content
   - Maintains history automatically
   - Clear separation between draft and approved states

3. **Why deepdiff?**
   - Industry-standard Python library
   - Handles nested JSON structures
   - Provides detailed change information
   - Supports custom comparison logic

## Notes

- Template master status remains APPROVED even when draft versions exist
- Approvers can see both the current approved content and pending changes
- Rejected changes are tracked but not merged
- Version numbers never decrease or reuse
- Each version maintains full content snapshot (not just diffs)
