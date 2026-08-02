/**
 * EditorSelectionContext - Modern ProseMirror-based selection management
 * 
 * Replaces legacy Canvas-based SelectionContext with native ProseMirror selection.
 * Works directly with Tiptap editor state instead of managing separate element arrays.
 */

import { createContext, useContext, useMemo, useState, type ReactNode, useEffect } from 'react';
import type { Editor } from '@tiptap/react';
import type { Node as ProseMirrorNode } from '@tiptap/pm/model';

/**
 * Content types based on ProseMirror node types
 */
export type ContentType = 
  | 'doc'           // Root document
  | 'paragraph'     // Text paragraph
  | 'heading'       // Heading (h1-h6)
  | 'text'          // Plain text
  | 'image'         // Image node
  | 'table'         // Table structure
  | 'tableRow'      // Table row
  | 'tableCell'     // Table cell
  | 'tableHeader'   // Table header cell
  | 'bulletList'    // Bullet list
  | 'orderedList'   // Numbered list
  | 'listItem'      // List item
  | 'horizontalRule' // Horizontal line
  | 'hardBreak'     // Line break
  | 'codeBlock'     // Code block
  | 'blockquote'    // Quote block
  | 'variableChip'  // Custom variable node
  | 'link'          // Link mark
  | 'none';         // No selection

/**
 * Selection mode
 */
export type SelectionMode = 'text' | 'node' | 'none';

/**
 * Context value providing editor selection state
 */
interface EditorSelectionContextValue {
  // Editor instance
  editor: Editor | null;
  
  // Selection state
  hasSelection: boolean;
  selectionEmpty: boolean;
  selectionMode: SelectionMode;
  
  // Content type at selection
  contentType: ContentType;
  
  // Selection range
  selectionFrom: number;
  selectionTo: number;
  
  // Selected node (if node selection)
  selectedNode: ProseMirrorNode | null;
  
  // Active marks (bold, italic, etc.)
  activeMarks: Set<string>;
  
  // Helper methods
  isActive: (name: string, attrs?: Record<string, any>) => boolean;
  getNodeAttrs: (name: string) => Record<string, any> | null;
  
  // Editing mode
  isEditable: boolean;
  isFocused: boolean;
}

const EditorSelectionContext = createContext<EditorSelectionContextValue | null>(null);

interface EditorSelectionProviderProps {
  children: ReactNode;
  editor: Editor | null;
}

/**
 * Provider for editor selection state
 * Automatically updates when editor selection changes
 */
export function EditorSelectionProvider({
  children,
  editor,
}: EditorSelectionProviderProps) {
  const [, forceUpdate] = useState({});

  // Force re-render when editor selection changes
  useEffect(() => {
    if (!editor) return;

    const handleUpdate = () => {
      forceUpdate({});
    };

    editor.on('selectionUpdate', handleUpdate);
    editor.on('transaction', handleUpdate);

    return () => {
      editor.off('selectionUpdate', handleUpdate);
      editor.off('transaction', handleUpdate);
    };
  }, [editor]);

  const value = useMemo((): EditorSelectionContextValue => {
    if (!editor) {
      return {
        editor: null,
        hasSelection: false,
        selectionEmpty: true,
        selectionMode: 'none',
        contentType: 'none',
        selectionFrom: 0,
        selectionTo: 0,
        selectedNode: null,
        activeMarks: new Set(),
        isActive: () => false,
        getNodeAttrs: () => null,
        isEditable: false,
        isFocused: false,
      };
    }

    const { state, view } = editor;
    const { selection } = state;
    const { from, to, empty } = selection;

    // Determine selection mode
    let mode: SelectionMode = 'none';
    if (!empty) {
      mode = selection instanceof view.state.selection.constructor ? 'text' : 'node';
    }

    // Get selected node (for node selections)
    const selectedNode = selection instanceof view.state.selection.constructor
      ? null
      : (selection as any).node ?? null;

    // Get content type at selection
    const $from = selection.$from;
    const node = $from.parent;
    let type: ContentType = 'none';

    if (selectedNode) {
      type = selectedNode.type.name as ContentType;
    } else if (node) {
      type = node.type.name as ContentType;
    }

    // Get active marks at selection
    const marks = new Set<string>();
    state.storedMarks?.forEach(mark => marks.add(mark.type.name));
    selection.$from.marks().forEach(mark => marks.add(mark.type.name));

    // Helper: Check if node/mark is active
    const isActive = (name: string, attrs?: Record<string, any>) => {
      return editor.isActive(name, attrs);
    };

    // Helper: Get node attributes
    const getNodeAttrs = (name: string) => {
      const attrs = editor.getAttributes(name);
      return Object.keys(attrs).length > 0 ? attrs : null;
    };

    return {
      editor,
      hasSelection: !empty,
      selectionEmpty: empty,
      selectionMode: mode,
      contentType: type,
      selectionFrom: from,
      selectionTo: to,
      selectedNode,
      activeMarks: marks,
      isActive,
      getNodeAttrs,
      isEditable: editor.isEditable,
      isFocused: editor.isFocused,
    };
  }, [editor]);

  return (
    <EditorSelectionContext.Provider value={value}>
      {children}
    </EditorSelectionContext.Provider>
  );
}

/**
 * Hook to access editor selection state
 * @throws Error if used outside EditorSelectionProvider
 */
export function useEditorSelection() {
  const context = useContext(EditorSelectionContext);
  
  if (!context) {
    throw new Error('useEditorSelection must be used within EditorSelectionProvider');
  }
  
  return context;
}

/**
 * Hook to get formatting state at current selection
 * Returns active text formatting (bold, italic, underline, etc.)
 */
export function useFormattingState() {
  const { editor, activeMarks, isActive } = useEditorSelection();

  return useMemo(() => {
    if (!editor) {
      return {
        bold: false,
        italic: false,
        underline: false,
        strike: false,
        code: false,
        link: false,
        highlight: false,
      };
    }

    return {
      bold: isActive('bold'),
      italic: isActive('italic'),
      underline: isActive('underline'),
      strike: isActive('strike'),
      code: isActive('code'),
      link: isActive('link'),
      highlight: isActive('highlight'),
    };
  }, [editor, activeMarks, isActive]);
}

/**
 * Hook to get current text alignment
 */
export function useTextAlignment() {
  const { editor, isActive } = useEditorSelection();

  return useMemo(() => {
    if (!editor) return 'left';
    
    if (isActive('textAlign', { textAlign: 'left' })) return 'left';
    if (isActive('textAlign', { textAlign: 'center' })) return 'center';
    if (isActive('textAlign', { textAlign: 'right' })) return 'right';
    if (isActive('textAlign', { textAlign: 'justify' })) return 'justify';
    
    return 'left';
  }, [editor, isActive]);
}

/**
 * Hook to get heading level at selection (if any)
 */
export function useHeadingLevel() {
  const { editor, contentType, getNodeAttrs } = useEditorSelection();

  return useMemo(() => {
    if (!editor || contentType !== 'heading') return null;
    
    const attrs = getNodeAttrs('heading');
    return attrs?.level ?? null;
  }, [editor, contentType, getNodeAttrs]);
}
