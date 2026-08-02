# 🔄 SelectionContext Refactoring - Migration Guide

**Status:** In Progress  
**Goal:** Migrate from Canvas-based SelectionContext to ProseMirror-native EditorSelectionContext  
**Impact:** Cleaner architecture, native selection handling, +3% migration score (87% → 90%)

---

## 📊 Current Status

### ✅ Completed
- [x] Created `EditorSelectionContext` - ProseMirror-native selection management
- [x] Created `ModernPropertyPanel` - Example property panel using new context
- [x] Created helper hooks (`useFormattingState`, `useTextAlignment`, `useHeadingLevel`)

### ⏳ In Progress
- [ ] Update `TemplateForm.tsx` to use new context
- [ ] Deprecate legacy `SelectionContext.tsx`
- [ ] Update property panels to use new context
- [ ] Remove Canvas-style element selection

---

## 🔄 Migration Steps

### Step 1: Add EditorSelectionProvider to TemplateForm

**Location:** `eddp_frontend/src/features/templates/components/TemplateForm.tsx`

```tsx
import { EditorSelectionProvider } from '../contexts/EditorSelectionContext';
import { ModernPropertyPanel } from './properties/ModernPropertyPanel';

// Inside TemplateForm component, wrap the editor:
<EditorSelectionProvider editor={editor}>
  <Box display="flex" height="100vh">
    {/* Left sidebar - property panel */}
    <Box width={300} sx={{ borderRight: 1, borderColor: 'divider', overflow: 'auto' }}>
      <ModernPropertyPanel
        pageSize={pageSettings.size}
        orientation={pageSettings.orientation}
        onPageSizeChange={(size) => setPageSettings(prev => ({ ...prev, size }))}
        onOrientationChange={(orientation) => setPageSettings(prev => ({ ...prev, orientation }))}
      />
    </Box>

    {/* Main editor area */}
    <Box flex={1} sx={{ overflow: 'auto', p: 3 }}>
      <EditorContent editor={editor} />
    </Box>
  </Box>
</EditorSelectionProvider>
```

---

### Step 2: Update Components to Use New Context

**Before (Legacy Canvas-based):**
```tsx
import { useSelection } from '../../contexts/SelectionContext';

function MyComponent() {
  const { selectedElements, primaryElement } = useSelection();
  
  // Access Canvas properties (x, y, width, height)
  const element = primaryElement;
  return <div>X: {element?.x}, Y: {element?.y}</div>;
}
```

**After (Modern ProseMirror-based):**
```tsx
import { useEditorSelection, useFormattingState } from '../../contexts/EditorSelectionContext';

function MyComponent() {
  const { editor, contentType, hasSelection } = useEditorSelection();
  const formatting = useFormattingState();
  
  // Access editor state and formatting
  return (
    <div>
      Content type: {contentType}
      {formatting.bold && 'Bold is active'}
    </div>
  );
}
```

---

### Step 3: Available Hooks

#### `useEditorSelection()`
Main hook for accessing editor selection state.

```tsx
const {
  editor,              // Tiptap editor instance
  hasSelection,        // true if anything is selected
  selectionEmpty,      // true if selection is empty (cursor position)
  selectionMode,       // 'text' | 'node' | 'none'
  contentType,         // Type of content at selection (paragraph, heading, etc.)
  selectionFrom,       // Start position
  selectionTo,         // End position
  selectedNode,        // Selected ProseMirror node (if node selection)
  activeMarks,         // Set of active marks (bold, italic, etc.)
  isActive,            // Check if node/mark is active
  getNodeAttrs,        // Get node attributes
  isEditable,          // Is editor editable
  isFocused,           // Is editor focused
} = useEditorSelection();
```

#### `useFormattingState()`
Get active text formatting at selection.

```tsx
const {
  bold,      // boolean
  italic,    // boolean
  underline, // boolean
  strike,    // boolean
  code,      // boolean
  link,      // boolean
  highlight, // boolean
} = useFormattingState();
```

#### `useTextAlignment()`
Get current text alignment.

```tsx
const alignment = useTextAlignment(); // 'left' | 'center' | 'right' | 'justify'
```

#### `useHeadingLevel()`
Get heading level (if selection is in heading).

```tsx
const level = useHeadingLevel(); // 1 | 2 | 3 | 4 | 5 | 6 | null
```

---

### Step 4: Applying Formatting

Use editor commands directly:

```tsx
const { editor } = useEditorSelection();

// Toggle formatting
editor.chain().focus().toggleBold().run();
editor.chain().focus().toggleItalic().run();
editor.chain().focus().toggleUnderline().run();

// Set alignment
editor.chain().focus().setTextAlign('center').run();

// Set heading
editor.chain().focus().setHeading({ level: 1 }).run();

// Set paragraph
editor.chain().focus().setParagraph().run();

// Insert content
editor.chain().focus().insertContent('Hello World').run();
```

---

## 🗑️ What Gets Removed

### Deprecated Concepts (Canvas-based)
- ❌ `DesignerElement` type with x, y, width, height
- ❌ `selectedElements` array
- ❌ `primaryElement` 
- ❌ `selectElement()` / `clearSelection()` methods
- ❌ Manual selection state management
- ❌ Element ID-based selection tracking

### Replaced By (ProseMirror-native)
- ✅ `editor.state.selection` (built-in)
- ✅ `contentType` (paragraph, heading, etc.)
- ✅ `selectionMode` (text, node, none)
- ✅ `useFormattingState()` hook
- ✅ Native editor commands
- ✅ Automatic selection updates

---

## 📋 Component Migration Checklist

### Components to Update
- [ ] `TemplateForm.tsx` - Add EditorSelectionProvider
- [ ] `ContextualPropertyPanel.tsx` - Use useEditorSelection
- [ ] `ContextToolbarManager.tsx` - Use useEditorSelection
- [ ] `PageToolbar.tsx` - Update if needed
- [ ] `ParagraphToolbar.tsx` - Use new hooks
- [ ] `FieldToolbar.tsx` - Use new hooks
- [ ] `TableToolbar.tsx` - Use new hooks

### Files to Deprecate
- [ ] `SelectionContext.tsx` - Mark as deprecated, add warning
- [ ] Legacy property panels that use DesignerElement

---

## 🎯 Benefits of New Architecture

### Performance
- ✅ No manual re-renders on selection change
- ✅ Uses ProseMirror's optimized selection system
- ✅ Fewer state updates

### Developer Experience
- ✅ Type-safe with ProseMirror types
- ✅ No need to manage selection state manually
- ✅ Direct access to editor commands
- ✅ Consistent with Tiptap patterns

### Maintainability
- ✅ Removes 800+ lines of legacy selection code
- ✅ No Canvas coordinate tracking
- ✅ Standard ProseMirror selection model
- ✅ Easier to debug

---

## 📖 Example: Complete Component

```tsx
import { useEditorSelection, useFormattingState } from '../contexts/EditorSelectionContext';
import { Box, IconButton, Stack } from '@mui/material';
import FormatBoldIcon from '@mui/icons-material/FormatBold';
import FormatItalicIcon from '@mui/icons-material/FormatItalic';

export function FormattingToolbar() {
  const { editor, hasSelection } = useEditorSelection();
  const { bold, italic } = useFormattingState();

  if (!hasSelection || !editor) {
    return null;
  }

  return (
    <Stack direction="row" spacing={1}>
      <IconButton
        size="small"
        onClick={() => editor.chain().focus().toggleBold().run()}
        color={bold ? 'primary' : 'default'}
      >
        <FormatBoldIcon />
      </IconButton>
      
      <IconButton
        size="small"
        onClick={() => editor.chain().focus().toggleItalic().run()}
        color={italic ? 'primary' : 'default'}
      >
        <FormatItalicIcon />
      </IconButton>
    </Stack>
  );
}
```

---

## 🚀 Next Steps

1. **Integrate EditorSelectionProvider** into TemplateForm
2. **Update one property panel** as proof of concept
3. **Test thoroughly** - ensure formatting works
4. **Migrate remaining components** one by one
5. **Remove legacy SelectionContext** after all components updated
6. **Update tests** to use new context

---

## 📊 Impact on Migration Score

**Current:** 87%  
**After Refactor:** 90%  
**Improvement:** +3%

**Component Breakdown:**
- SelectionContext: 40% → 95% (+55%)
- Overall Frontend: 82% → 85% (+3%)
- Overall Platform: 87% → 90% (+3%)

---

## ⚠️ Important Notes

1. **Backward Compatibility:** Keep legacy SelectionContext until all components migrated
2. **Page Properties:** Still needed for document-level settings (page size, orientation)
3. **Variable System:** Already uses ProseMirror nodes (VariableChipNode)
4. **Testing:** Test selection behavior after each component migration

---

**Status:** Ready for integration  
**Next Action:** Update TemplateForm.tsx to use EditorSelectionProvider  
**Estimated Time:** 2-4 hours for complete migration
