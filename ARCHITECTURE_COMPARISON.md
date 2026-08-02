# Architecture Comparison: Canvas vs Tiptap/ProseMirror

## Visual Architecture Diagrams

### OLD ARCHITECTURE (Canvas/Figma Style)

```
┌─────────────────────────────────────────────────────────────┐
│                    CANVAS EDITOR                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Page 1 (794px × 1123px)                              │  │
│  │                                                        │  │
│  │  Element 1: {                                         │  │
│  │    id: "abc123",                                      │  │
│  │    type: "heading",                                   │  │
│  │    x: 40,  ← Absolute position                       │  │
│  │    y: 100, ← Absolute position                       │  │
│  │    width: 700,                                        │  │
│  │    height: 48,                                        │  │
│  │    rotation: 0,                                       │  │
│  │    zIndex: 1,  ← Layer ordering                      │  │
│  │    text: "Chapter 1"                                  │  │
│  │  }                                                     │  │
│  │                                                        │  │
│  │  Element 2: {                                         │  │
│  │    x: 40, y: 160, width: 700, height: 120, ...       │  │
│  │  }                                                     │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

Data Structure:
{
  "elements": [
    { id, type, x, y, width, height, rotation, zIndex, ... },
    { id, type, x, y, width, height, rotation, zIndex, ... },
    ...
  ]
}

Problems:
❌ Elements positioned absolutely (like Figma/Sketch)
❌ Overlapping elements cause rendering issues
❌ No text reflow - fixed dimensions
❌ Manual position calculation
❌ Z-index conflicts
❌ Page breaks require coordinate tracking
```

---

### NEW ARCHITECTURE (Tiptap/ProseMirror)

```
┌─────────────────────────────────────────────────────────────┐
│                 TIPTAP EDITOR                                 │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Document (flows like Word/Google Docs)               │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │ Heading: "Chapter 1"                             │ │  │
│  │  │   type: "heading", level: 1                      │ │  │
│  │  │   attrs: { id: "h1", align: "left" }             │ │  │
│  │  │   marks: [bold]                                  │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │ Paragraph: "This is the introduction..."         │ │  │
│  │  │   type: "paragraph"                              │ │  │
│  │  │   content: [text nodes with marks]               │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │ Table: 3×2                                       │ │  │
│  │  │   type: "table"                                  │ │  │
│  │  │   content: [tableRow, tableRow, tableRow]        │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

Data Structure:
{
  "prosemirror_json": {
    "type": "doc",
    "content": [
      {
        "type": "heading",
        "attrs": { "level": 1, "id": "h1" },
        "content": [
          { "type": "text", "text": "Chapter 1", "marks": [{"type": "bold"}] }
        ]
      },
      {
        "type": "paragraph",
        "content": [
          { "type": "text", "text": "This is..." }
        ]
      },
      ...
    ]
  }
}

Benefits:
✅ Content flows naturally (like Word)
✅ Automatic text reflow
✅ Hierarchical structure (tree, not flat array)
✅ No coordinate tracking
✅ Built-in undo/redo
✅ Real-time collaboration support
✅ Semantic structure (heading > paragraph > text)
```

---

## Data Flow Comparison

### OLD FLOW (Canvas)

```
User Action
    ↓
Canvas Event (mouseDown, drag, etc.)
    ↓
Update Element Position { x: newX, y: newY }
    ↓
Re-render Canvas (redraw all elements)
    ↓
Save elements[] to database
    ↓
Load: Sort by (page, y) → position on canvas
```

### NEW FLOW (ProseMirror)

```
User Action
    ↓
Editor Command (insertText, toggleBold, etc.)
    ↓
ProseMirror Transaction
    ↓
Update Document State (immutable)
    ↓
Re-render Changed Nodes Only
    ↓
Save prosemirror_json to database
    ↓
Load: Parse JSON → render document tree
```

---

## Diff & Version Control Comparison

### OLD (Canvas Element Comparison)

```python
# Compared x, y coordinates
if old_element.x != new_element.x or old_element.y != new_element.y:
    changes.append({
        "type": "POSITION_CHANGED",
        "oldPosition": {"x": old_element.x, "y": old_element.y},
        "newPosition": {"x": new_element.x, "y": new_element.y}
    })

# Sorted by position to match elements
elements.sort(key=lambda e: (e.page, e.y, e.x))
```

**Problems:**
- ❌ Position changes are noise (not semantic)
- ❌ Hard to match moved elements
- ❌ Can't detect reordering vs movement

### NEW (ProseMirror Semantic Comparison)

```python
# Compared document structure
if old_node.type != new_node.type:
    changes.append({
        "type": "NODE_TYPE_CHANGED",
        "path": "doc.content[2]",
        "oldType": "paragraph",
        "newType": "heading"
    })

if old_node.text != new_node.text:
    changes.append({
        "type": "TEXT_MODIFIED",
        "path": "doc.content[2].content[0]",
        "oldText": "Hello",
        "newText": "Hello World"
    })
```

**Benefits:**
- ✅ Semantic changes only (text, structure, formatting)
- ✅ Path-based addressing
- ✅ Can detect reordering
- ✅ No false positives from layout changes

---

## Word Import Comparison

### OLD (Canvas Parser)

```
DOCX File
    ↓
python-docx (parse structure)
    ↓
FOR EACH paragraph:
    element = {
        id: uuid(),
        x: 40,  ← Manual positioning
        y: current_y_position,
        width: 760,
        height: calculated_height,
        text: paragraph.text
    }
    current_y_position += height + 10
    ↓
Return elements[]
```

**Problems:**
- ❌ Loses document structure
- ❌ Manual position calculation
- ❌ Tables become text strings
- ❌ Formatting partially lost

### NEW (ProseMirror Parser - PROPOSED)

```
DOCX File
    ↓
Mammoth.js (convert to HTML)
    ↓
ProseMirror Parser (HTML → ProseMirror JSON)
    ↓
Return {
  "prosemirror_json": {
    "type": "doc",
    "content": [
      { "type": "heading", ... },
      { "type": "paragraph", ... },
      { "type": "table", ... }
    ]
  }
}
```

**Benefits:**
- ✅ Preserves document structure
- ✅ No manual positioning
- ✅ Tables remain tables
- ✅ Full formatting preserved

---

## Variable System Comparison

### OLD (Text Tokens in Canvas Elements)

```javascript
// Variable as text string
element = {
  type: "paragraph",
  text: "Hello {{customer_name}}, your balance is {{account_balance}}",
  x: 40, y: 100
}

// Rendering
html = element.text
  .replace(/\{\{customer_name\}\}/g, data.customer_name)
  .replace(/\{\{account_balance\}\}/g, data.account_balance)
```

**Problems:**
- ❌ Variables not first-class entities
- ❌ Hard to validate
- ❌ Can't style variables differently
- ❌ Regex-based replacement fragile

### NEW (Custom ProseMirror Nodes - PROPOSED)

```javascript
// Variable as custom node
{
  "type": "paragraph",
  "content": [
    { "type": "text", "text": "Hello " },
    {
      "type": "variable",  // Custom node
      "attrs": {
        "variableKey": "customer_name",
        "variableLabel": "Customer Name",
        "variableType": "string"
      }
    },
    { "type": "text", "text": ", your balance is " },
    {
      "type": "variable",
      "attrs": {
        "variableKey": "account_balance",
        "variableLabel": "Account Balance",
        "variableType": "currency"
      }
    }
  ]
}

// Rendering
editor.view.dom.querySelectorAll('[data-variable]').forEach(node => {
  const key = node.getAttribute('data-variable')
  node.textContent = data[key]
})
```

**Benefits:**
- ✅ Variables are structured data
- ✅ Type checking (string, number, currency, etc.)
- ✅ Visual distinction in editor
- ✅ Validation errors shown inline
- ✅ Autocomplete support

---

## Selection & Editing Comparison

### OLD (Canvas Selection)

```javascript
// Selected elements array
selectedElements = [element1, element2, element3]

// Multi-select by ID
selectedIds = ["abc123", "def456", "ghi789"]

// Operations
moveElements(selectedElements, dx, dy)
resizeElements(selectedElements, newWidth, newHeight)
deleteElements(selectedElements)
```

**Problems:**
- ❌ Managing element arrays manually
- ❌ Multi-element operations complex
- ❌ Can't select partial text

### NEW (ProseMirror Selection)

```javascript
// Selection as document range
selection = {
  anchor: 45,  // Start position in document
  head: 103    // End position in document
}

// Text selection (built-in)
editor.state.selection.from  // 45
editor.state.selection.to    // 103

// Operations (built-in)
editor.commands.deleteSelection()
editor.commands.toggleBold()
editor.commands.setTextAlign('center')
```

**Benefits:**
- ✅ Built-in selection system
- ✅ Text-level selection
- ✅ Range-based operations
- ✅ Undo/redo works automatically

---

## Summary Table

| Feature | Canvas/Figma | Tiptap/ProseMirror |
|---------|--------------|-------------------|
| **Positioning** | Absolute (x, y) | Document flow |
| **Data Model** | Flat array | Tree structure |
| **Text Flow** | Fixed boxes | Automatic reflow |
| **Structure** | Visual only | Semantic (heading, paragraph, etc.) |
| **Editing** | Click & drag | Text editing |
| **Version Control** | Position diffs | Semantic diffs |
| **Undo/Redo** | Manual | Built-in |
| **Collaboration** | Complex | Native support |
| **Accessibility** | Poor | Excellent |
| **Variables** | Text tokens | Custom nodes |
| **Validation** | Manual | Schema-based |
| **Word Import** | Lossy | Lossless |
| **PDF Export** | Direct | Via HTML |

---

## Migration Strategy Summary

### Phase 1: Stop Generating Canvas Elements
- Delete legacy converter functions
- Rewrite Word parser
- Update API responses

### Phase 2: Update Type System
- Remove `DesignerElement` interface
- Use ProseMirror types
- Update SelectionContext

### Phase 3: Fix Diff & Review
- Remove position-based change detection
- Focus on semantic changes
- Update review UI

### Phase 4: Data Migration
- Convert existing Canvas content to ProseMirror
- Validate all templates
- Archive legacy backups

### Phase 5: Clean Up
- Remove coordinate references
- Update documentation
- Delete unused code

---

**Key Insight:** Canvas/Figma editors are for **visual design** (graphics, layouts, wireframes). ProseMirror is for **document editing** (reports, contracts, letters). They are fundamentally different paradigms and cannot coexist cleanly.

The platform must commit fully to one or the other. Since Tiptap/ProseMirror is already implemented and working, the path forward is to complete the migration by removing all Canvas dependencies.
