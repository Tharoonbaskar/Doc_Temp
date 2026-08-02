# Quick Start: Template Version Control

## Installation

1. **Install Python dependency:**
   ```cmd
   cd "D:\Document Template Generator V1\eddp_backend"
   venv\Scripts\pip.exe install deepdiff==8.0.1
   ```

2. **Run database migrations:**
   ```cmd
   cd "D:\Document Template Generator V1\eddp_backend"
   venv\Scripts\python.exe manage.py makemigrations templates
   venv\Scripts\python.exe manage.py migrate
   ```

3. **Start backend server:**
   ```cmd
   cd "D:\Document Template Generator V1\eddp_backend"
   venv\Scripts\python.exe manage.py runserver
   ```

4. **Start frontend (in new terminal):**
   ```cmd
   cd "D:\Document Template Generator V1\eddp_frontend"
   npm run dev
   ```

## User Guide

### As a Template Editor

1. **Create Initial Template**
   - Go to "Document Create or Delete"
   - Create a new template
   - Add content using the designer
   - Save as DRAFT
   - Click "Send for Review"

2. **Edit Approved Template**
   - Find an APPROVED template
   - Click Edit
   - Make your changes (add, modify, or delete elements)
   - Click Save
   - **System automatically creates v2.0 DRAFT in background**
   - You'll see a success message confirming draft version created

### As an Approver

1. **Initial Approval (v1.0)**
   - Go to "Document Approval"
   - Find template with status "For Review"
   - Click "Review"
   - Set effective date
   - Click "Approve"
   - Template becomes v1.0 APPROVED

2. **Review Version Changes (v2.0+)**
   - Go to "Document Approval"
   - Find template with draft version pending
   - Click "Review Version v2.0"
   - See summary: Total changes, Added, Modified, Deleted
   - Review each element change:

3. **Approve/Reject Individual Changes**
   For each change, you'll see:
   - **Green box** = New content added
   - **Orange boxes** = Original (crossed out) vs Modified content
   - **Red box** = Deleted content (crossed out)
   
   Actions per change:
   - Click **Approve** ✓ to accept the change
   - Click **Reject** ✗ to decline the change  
   - Click **Undo** ↺ to revert to original
   - Add optional comment

4. **Final Approval**
   - Once all changes reviewed (no pending left)
   - Green alert appears: "All changes reviewed"
   - Click "Approve Version" button
   - Only APPROVED changes get merged into v2.0
   - Template content updated

## Example Scenarios

### Scenario 1: Simple Addition
**Editor Action:**
- Opens approved template v1.0
- Adds a new heading "Conclusion"
- Saves

**Approver View:**
```
┌─────────────────────────────────┐
│ ADDED - heading_conclusion      │
│ Status: Pending Review          │
├─────────────────────────────────┤
│ New Content:                    │
│ ┌─────────────────────────────┐ │
│ │ Conclusion                  │ │ (green background)
│ │ Font: Arial, Size: 16       │ │
│ └─────────────────────────────┘ │
│                                 │
│ [✓ Approve] [✗ Reject] [↺]     │
└─────────────────────────────────┘
```

### Scenario 2: Modification
**Editor Action:**
- Changes "Dear Customer" to "Dear Valued Customer"
- Saves

**Approver View:**
```
┌─────────────────────────────────┐
│ MODIFIED - text_greeting        │
│ Status: Pending Review          │
├─────────────────────────────────┤
│ Original:                       │
│ ┌─────────────────────────────┐ │
│ │ Dear Customer               │ │ (red bg, strikethrough)
│ └─────────────────────────────┘ │
│                                 │
│ Modified:                       │
│ ┌─────────────────────────────┐ │
│ │ Dear Valued Customer        │ │ (green background)
│ └─────────────────────────────┘ │
│                                 │
│ [✓ Approve] [✗ Reject] [↺]     │
└─────────────────────────────────┘
```

### Scenario 3: Deletion
**Editor Action:**
- Removes the disclaimer paragraph
- Saves

**Approver View:**
```
┌─────────────────────────────────┐
│ DELETED - para_disclaimer       │
│ Status: Pending Review          │
├─────────────────────────────────┤
│ Deleted Content:                │
│ ┌─────────────────────────────┐ │
│ │ This is not legal advice... │ │ (red bg, strikethrough)
│ └─────────────────────────────┘ │
│                                 │
│ [✓ Approve] [✗ Reject] [↺]     │
└─────────────────────────────────┘
```

### Scenario 4: Mixed Approval
**Reviewer Actions:**
1. Approves the new heading
2. Rejects the modified greeting (wants original)
3. Approves the deletion

**Result:**
- v2.0 created with:
  - ✓ New "Conclusion" heading added
  - ✗ Greeting stays as "Dear Customer" (rejected change)
  - ✓ Disclaimer removed

## UI Navigation

### Template Editor Flow
```
Document Create or Delete
  → [Create Template]
  → Designer (add elements)
  → [Save Draft]
  → [Send for Review]
  → (Wait for approval)
  → ✓ Template approved as v1.0
  → [Edit] (make changes)
  → [Save]
  → System creates v2.0 DRAFT automatically
```

### Approver Flow
```
Document Approval
  → See "For Review" templates
  → [Review] (initial approval)
  → Set effective date
  → [Approve] → becomes v1.0
  
Later, when v2.0 DRAFT exists:
  → See template with version indicator
  → [Review Version v2.0]
  → Review each change individually
  → Approve/Reject/Revert each
  → [Approve Version] when all reviewed
  → v2.0 becomes APPROVED
```

## Key Benefits

✅ **Never lose approved content** - Original versions always preserved
✅ **Granular control** - Approve some changes, reject others
✅ **Clear visual feedback** - Color-coded additions (green), modifications (orange), deletions (red)
✅ **Full audit trail** - Who approved what and when
✅ **Automatic** - No manual version creation needed
✅ **VS Code-like** - Familiar UX for developers

## Troubleshooting

**Q: I edited an approved template but don't see v2.0?**
A: Check the API response - the backend returns the new version details. Refresh the page.

**Q: All changes show as pending, what do I do?**
A: Review each change using Approve/Reject/Revert buttons. Final approval only works when all changes are reviewed.

**Q: I rejected a change but want to undo that?**
A: Click the Revert button to reset the change back to Pending status, then approve it.

**Q: Can I approve without reviewing all changes?**
A: No - this ensures deliberate review of every modification. You must review all changes first.

**Q: What happens to rejected changes?**
A: They're tracked in the database but not merged into the final version. The original content is retained.

## Next Steps

After testing the basic workflow:
1. Try editing an approved template with multiple changes
2. Practice granular approval - approve some, reject others
3. Check the version history
4. Review the audit trail

See [VERSION_CONTROL_SYSTEM.md](./VERSION_CONTROL_SYSTEM.md) for complete technical documentation.
