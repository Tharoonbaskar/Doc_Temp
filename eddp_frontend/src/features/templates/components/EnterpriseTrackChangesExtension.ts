import { Extension } from '@tiptap/core';
import type { Editor } from '@tiptap/react';
import { Plugin, PluginKey } from '@tiptap/pm/state';
import { Decoration, DecorationSet } from '@tiptap/pm/view';
import type { Node as ProseMirrorNode } from '@tiptap/pm/model';

import type { ElementChange, InlineDiffSegment, SemanticChangeType } from '../types';

type TrackChangesPluginState = {
  decorations: DecorationSet;
};

type TextSnapshot = {
  oldText: string;
  newText: string;
};

type TokenDelta = {
  addedCount: number;
  removedCount: number;
  overlapCount: number;
  oldCount: number;
  newCount: number;
  similarity: number;
};

const pluginKey = new PluginKey<TrackChangesPluginState>('enterpriseTrackChanges');

const toObject = (value: unknown): Record<string, unknown> => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    return {};
  }
  return value as Record<string, unknown>;
};

const getTextValue = (value: unknown): string => {
  if (typeof value === 'string') {
    return value.replace(/\r\n/g, '\n');
  }

  const obj = toObject(value);
  const oldText = obj.oldText;
  if (typeof oldText === 'string') {
    return oldText.replace(/\r\n/g, '\n');
  }

  const newText = obj.newText;
  if (typeof newText === 'string') {
    return newText.replace(/\r\n/g, '\n');
  }

  const textValue = obj.text;
  if (typeof textValue === 'string') {
    return textValue.replace(/\r\n/g, '\n');
  }

  const labelValue = obj.label;
  if (typeof labelValue === 'string') {
    return labelValue.replace(/\r\n/g, '\n');
  }

  const bindingValue = obj.binding;
  if (typeof bindingValue === 'string' && bindingValue.trim()) {
    return `{{${bindingValue.trim()}}}`;
  }

  const readFromPm = (node: unknown): string => {
    if (!node || typeof node !== 'object') {
      return '';
    }

    const record = node as Record<string, unknown>;
    const parts: string[] = [];
    const text = record.text;
    if (typeof text === 'string') {
      parts.push(text);
    }

    const attrs = record.attrs;
    if (attrs && typeof attrs === 'object') {
      const attrsRecord = attrs as Record<string, unknown>;
      const binding = attrsRecord.binding;
      const field = attrsRecord.field;
      if (typeof binding === 'string' && binding.trim()) {
        parts.push(`{{${binding.trim()}}}`);
      } else if (typeof field === 'string' && field.trim()) {
        parts.push(`<${field.trim()}>`);
      }
    }

    const content = record.content;
    if (Array.isArray(content)) {
      content.forEach((child) => {
        const childText = readFromPm(child);
        if (childText) {
          parts.push(childText);
        }
      });
    }

    return parts.join('');
  };

  const pmText = readFromPm(obj);
  if (pmText) {
    return pmText;
  }

  return '';
};

const getTextSnapshot = (change: ElementChange): TextSnapshot => ({
  oldText: change.old_text ?? getTextValue(change.old_value),
  newText: change.new_text ?? getTextValue(change.new_value),
});

const tokenize = (value: string): string[] =>
  value
    .toLowerCase()
    .split(/\s+/)
    .map((token) => token.trim())
    .filter(Boolean);

const toTokenDelta = (snapshot: TextSnapshot): TokenDelta => {
  const oldTokens = tokenize(snapshot.oldText);
  const newTokens = tokenize(snapshot.newText);

  const oldCounts = new Map<string, number>();
  oldTokens.forEach((token) => oldCounts.set(token, (oldCounts.get(token) || 0) + 1));

  const newCounts = new Map<string, number>();
  newTokens.forEach((token) => newCounts.set(token, (newCounts.get(token) || 0) + 1));

  let overlapCount = 0;
  oldCounts.forEach((count, token) => {
    overlapCount += Math.min(count, newCounts.get(token) || 0);
  });

  return {
    addedCount: Math.max(newTokens.length - overlapCount, 0),
    removedCount: Math.max(oldTokens.length - overlapCount, 0),
    overlapCount,
    oldCount: oldTokens.length,
    newCount: newTokens.length,
    similarity: overlapCount / Math.max(oldTokens.length, newTokens.length, 1),
  };
};

const refineTextSemanticType = (
  currentSemanticType: SemanticChangeType | null,
  snapshot: TextSnapshot,
): SemanticChangeType => {
  const oldText = snapshot.oldText;
  const newText = snapshot.newText;

  if (!oldText && newText) return 'TEXT_ADDED';
  if (oldText && !newText) return 'TEXT_REMOVED';

  const oldWithoutWhitespace = oldText.replace(/\s+/g, '');
  const newWithoutWhitespace = newText.replace(/\s+/g, '');
  if (oldWithoutWhitespace === newWithoutWhitespace && oldText !== newText) {
    return newText.length > oldText.length ? 'TEXT_ADDED' : 'TEXT_REMOVED';
  }

  if (oldText === newText) {
    return currentSemanticType && currentSemanticType !== 'UNKNOWN_CHANGE'
      ? currentSemanticType
      : 'TEXT_MODIFIED';
  }

  const tokenDelta = toTokenDelta(snapshot);
  if (!tokenDelta.newCount && tokenDelta.oldCount) return 'TEXT_REMOVED';
  if (!tokenDelta.oldCount && tokenDelta.newCount) return 'TEXT_ADDED';

  const isPureAddition = tokenDelta.removedCount === 0 && tokenDelta.addedCount > 0;
  const isPureRemoval = tokenDelta.addedCount === 0 && tokenDelta.removedCount > 0;
  if (isPureAddition) return 'TEXT_ADDED';
  if (isPureRemoval) return 'TEXT_REMOVED';

  const meaningfulRewrite =
    tokenDelta.addedCount > 0
    && tokenDelta.removedCount > 0
    && tokenDelta.similarity < 0.35;

  if (meaningfulRewrite) {
    return 'TEXT_ADDED';
  }

  if (currentSemanticType && currentSemanticType !== 'UNKNOWN_CHANGE') {
    return currentSemanticType;
  }

  return 'TEXT_MODIFIED';
};

const resolveSemanticType = (change: ElementChange): SemanticChangeType => {
  const snapshot = getTextSnapshot(change);

  if (change.change_type === 'ADDED') return 'TEXT_ADDED';
  if (change.change_type === 'DELETED') return 'TEXT_REMOVED';

  if (change.semantic_type?.startsWith('TEXT_')) {
    return refineTextSemanticType(change.semantic_type, snapshot);
  }

  if (change.semantic_type && change.semantic_type !== 'UNKNOWN_CHANGE') {
    return change.semantic_type;
  }

  if (change.change_type === 'MODIFIED') {
    return refineTextSemanticType(null, snapshot);
  }

  if (change.change_type === 'ADDED') return 'TEXT_ADDED';
  if (change.change_type === 'DELETED') return 'TEXT_REMOVED';
  return 'TEXT_MODIFIED';
};

const classifyVisualClass = (semanticType: SemanticChangeType): string => {
  if (semanticType.endsWith('_ADDED')) return 'et-change-added';
  if (semanticType.endsWith('_REMOVED')) return 'et-change-removed';
  if (
    semanticType.includes('FONT') ||
    semanticType.includes('ALIGNMENT') ||
    semanticType.includes('MARGIN') ||
    semanticType.includes('PADDING') ||
    semanticType.includes('STYLE') ||
    semanticType.includes('PAGE_SIZE') ||
    semanticType.includes('ORIENTATION') ||
    semanticType.includes('BACKGROUND')
  ) {
    return 'et-change-format';
  }
  if (
    semanticType.includes('PAGE_BREAK') ||
    semanticType.includes('SECTION')
  ) {
    return 'et-change-position';
  }
  if (semanticType.includes('IMAGE')) return 'et-change-image';
  if (semanticType.includes('TABLE')) return 'et-change-table';
  if (semanticType.includes('VARIABLE')) return 'et-change-variable';
  return 'et-change-modified';
};

type MatchLocation = { from: number; to: number };

type TextBlockRange = {
  text: string;
  from: number;
  to: number;
};

const normalizeForMatch = (value: string): string =>
  value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const tokenOverlapScore = (candidate: string, source: string): number => {
  const normalizedCandidate = normalizeForMatch(candidate);
  const normalizedSource = normalizeForMatch(source);
  if (!normalizedCandidate || !normalizedSource) {
    return 0;
  }

  const candidateTokens = normalizedCandidate.split(' ').filter(Boolean);
  const sourceTokenSet = new Set(normalizedSource.split(' ').filter(Boolean));
  const overlap = candidateTokens.filter((token) => sourceTokenSet.has(token)).length;

  return overlap / Math.max(candidateTokens.length, 1);
};

const describeText = (value: string): string => {
  if (value === '') {
    return '(empty)';
  }
  return JSON.stringify(value);
};

const toDeletedWidgetText = (value: string): string => {
  if (!value) {
    return '';
  }
  if (/^\s+$/.test(value)) {
    return value
      .replace(/ /g, '␠')
      .replace(/\t/g, '⇥')
      .replace(/\n/g, '↵\n');
  }
  return value;
};

const buildMatchLocations = (doc: ProseMirrorNode, changes: ElementChange[]): Record<string, MatchLocation> => {
  const locations: Record<string, MatchLocation> = {};
  const textBlocks: TextBlockRange[] = [];

  doc.descendants((node, pos) => {
    if (!node.isTextblock) return false;

    const text = (node.textContent || '').trim();
    if (!text) return false;

    textBlocks.push({
      text,
      from: pos + 1,
      to: Math.max(pos + node.nodeSize - 1, pos + 2),
    });

    return false;
  });

  changes.forEach((change) => {
    const snapshot = getTextSnapshot(change);
    const oldDelta = (change.old_text ?? snapshot.oldText).replace(/\r\n/g, '\n');
    const newDelta = (change.new_text ?? snapshot.newText).replace(/\r\n/g, '\n');

    const isRemovalOnly =
      (change.change_type === 'DELETED' || change.change_type === 'MODIFIED')
      && Boolean(oldDelta)
      && !newDelta;

    const contextText = (
      change.new_context_text
      || change.old_context_text
      || newDelta
      || oldDelta
      || ''
    ).trim();

    if (isRemovalOnly) {
      let bestBlock: TextBlockRange | null = null;
      let bestScore = 0;

      for (const block of textBlocks) {
        const score = tokenOverlapScore(contextText || oldDelta, block.text);
        if (score > bestScore) {
          bestScore = score;
          bestBlock = block;
        }
      }

      if (bestBlock && bestScore >= 0.15) {
        locations[change.id] = {
          from: Math.max(bestBlock.to - 1, bestBlock.from),
          to: Math.max(bestBlock.to - 1, bestBlock.from),
        };
      }
      return;
    }

    const candidateRaw = newDelta || oldDelta || contextText;
    const candidate = candidateRaw.trim() || candidateRaw;
    if (!candidate) return;

    const rankedBlocks = [...textBlocks].sort((a, b) => {
      const aScore = tokenOverlapScore(contextText || candidate, a.text);
      const bScore = tokenOverlapScore(contextText || candidate, b.text);
      return bScore - aScore;
    });

    const lowerCandidate = candidate.toLowerCase();
    for (const block of rankedBlocks) {
      const lowerText = block.text.toLowerCase();
      const index = lowerText.indexOf(lowerCandidate);
      if (index < 0) continue;

      const from = block.from + index;
      const to = Math.max(from + candidate.length, from + 1);
      locations[change.id] = { from, to };
      return;
    }

    const fallbackBlock = rankedBlocks[0] ?? null;
    const fallbackScore = fallbackBlock ? tokenOverlapScore(contextText || candidate, fallbackBlock.text) : 0;
    if (fallbackBlock && fallbackScore >= 0.3) {
      locations[change.id] = {
        from: fallbackBlock.from,
        to: Math.max(fallbackBlock.to, fallbackBlock.from + 1),
      };
    }
  });

  return locations;
};

const buildTooltip = (change: ElementChange, semanticType: SemanticChangeType): string => {
  const snapshot = getTextSnapshot(change);
  const parts = [
    `Change Type: ${semanticType}`,
    `Changed From: ${describeText(snapshot.oldText)}`,
    `Changed To: ${describeText(snapshot.newText)}`,
    `Version: ${change.node_id || change.element_id}`,
    `Reviewer: ${change.reviewed_by_name || 'Unassigned'}`,
    `Date: ${change.updated_at || 'N/A'}`,
    `Status: ${change.approval_status}`,
  ];
  return parts.join('\n');
};

type ResolvedNode = {
  node: ProseMirrorNode;
  contentStart: number;
};

// Resolve a backend JSON index-path (e.g. "0.2.1") to a concrete ProseMirror
// node plus the document position where its content begins. The leading "0"
// refers to the doc node itself. This is deterministic and order-preserving,
// which is what eliminates the scrambled / mis-ordered highlighting produced by
// the previous fuzzy text-search approach.
const resolveNodeByPath = (doc: ProseMirrorNode, path?: string | null): ResolvedNode | null => {
  if (!path || typeof path !== 'string') return null;

  const parts = path.split('.').map((part) => part.trim()).filter(Boolean);
  if (parts.length && parts[0] === '0') {
    parts.shift(); // drop the doc node itself
  }

  let node: ProseMirrorNode = doc;
  let base = 0; // position where the current node's content starts

  for (const part of parts) {
    const idx = Number(part);
    if (!Number.isInteger(idx) || idx < 0 || idx >= node.childCount) {
      return null;
    }
    let childStart = base;
    for (let i = 0; i < idx; i += 1) {
      childStart += node.child(i).nodeSize;
    }
    node = node.child(idx);
    base = childStart + 1; // content start inside the child (block / textblock)
  }

  return { node, contentStart: base };
};

const reconstructNewText = (segments: InlineDiffSegment[]): string =>
  segments
    .filter((seg) => seg.op !== 'delete')
    .map((seg) => seg.text)
    .join('')
    .replace(/\r\n/g, '\n');

// Structural, order-preserving decoration builder driven by the ProseMirror JSON
// node-path and the ordered inline segments computed on the backend.
// Returns true if it fully handled the change, false to fall back to fuzzy mode.
const applyStructuralDecorations = (
  doc: ProseMirrorNode,
  change: ElementChange,
  decorations: Decoration[],
): boolean => {
  const segments = change.inline_segments;
  const path = change.new_path || change.old_path;
  if (!segments || !segments.length || !path) return false;

  const resolved = resolveNodeByPath(doc, path);
  if (!resolved || !resolved.node.isTextblock) return false;

  // Alignment guard: the reconstructed "new" text (equal + insert segments) must
  // match the rendered node text exactly, otherwise character offsets could drift
  // (e.g. paragraphs containing variable chips / non-text inline nodes). If it
  // cannot align, bail out and let the fuzzy matcher handle this change safely.
  const expectedNew = reconstructNewText(segments).replace(/\n+$/, '');
  const actualText = resolved.node.textContent.replace(/\r\n/g, '\n').replace(/\n+$/, '');
  if (expectedNew !== actualText) {
    return false;
  }

  const semanticType = resolveSemanticType(change);
  const tooltip = buildTooltip(change, semanticType);
  const statusClass = `et-status-${String(change.approval_status || '').toLowerCase()}`;
  let cursor = resolved.contentStart;

  segments.forEach((seg) => {
    if (!seg.text) return;

    if (seg.op === 'equal') {
      cursor += seg.text.length;
      return;
    }

    if (seg.op === 'insert') {
      const from = cursor;
      const to = cursor + seg.text.length;
      decorations.push(
        Decoration.inline(from, to, {
          class: ['et-change-inline', 'et-change-added', statusClass].join(' '),
          'data-change-id': change.id,
          'data-change-type': semanticType,
          'data-review-status': change.approval_status,
          title: tooltip,
        }),
      );
      cursor = to;
      return;
    }

    // delete: render a strike-through widget in-place; do NOT advance the cursor.
    const deletedText = seg.text;
    decorations.push(
      Decoration.widget(
        cursor,
        () => {
          const el = document.createElement('span');
          el.className = 'et-change-deleted-widget';
          el.setAttribute('data-change-id', change.id);
          el.setAttribute('data-change-type', semanticType);
          el.setAttribute('data-review-status', change.approval_status);
          el.title = tooltip;
          el.style.whiteSpace = 'pre-wrap';
          el.textContent = toDeletedWidgetText(deletedText);
          return el;
        },
        { side: -1 },
      ),
    );
  });

  return true;
};

// Legacy fuzzy matcher, retained as a safe fallback for changes that lack a
// node path / ordered segments, or that cannot be aligned structurally.
const applyFuzzyDecorations = (
  doc: ProseMirrorNode,
  changes: ElementChange[],
  decorations: Decoration[],
): void => {
  const locations = buildMatchLocations(doc, changes);

  changes.forEach((change) => {
    const location = locations[change.id];
    if (!location) return;

    const semanticType = resolveSemanticType(change);
    const baseClass = change.change_type === 'MODIFIED' ? 'et-change-modified' : classifyVisualClass(semanticType);
    const tooltip = buildTooltip(change, semanticType);
    const snapshot = getTextSnapshot(change);
    const oldDelta = (change.old_text ?? snapshot.oldText).replace(/\r\n/g, '\n');
    const newDelta = (change.new_text ?? snapshot.newText).replace(/\r\n/g, '\n');
    const isRemovalOnly =
      (change.change_type === 'DELETED' || change.change_type === 'MODIFIED')
      && Boolean(oldDelta)
      && !newDelta;

    if (change.change_type === 'DELETED' || (change.change_type === 'MODIFIED' && oldDelta !== newDelta && Boolean(oldDelta))) {
      const deletedText = oldDelta;

      if (deletedText) {
        decorations.push(
          Decoration.widget(location.from, () => {
            const el = document.createElement('span');
            el.className = 'et-change-deleted-widget';
            el.setAttribute('data-change-id', change.id);
            el.setAttribute('data-change-type', semanticType);
            el.setAttribute('data-review-status', change.approval_status);
            el.title = tooltip;
            el.style.whiteSpace = 'pre-wrap';
            el.textContent = toDeletedWidgetText(deletedText);
            return el;
          }),
        );
      }
    }

    const inlineClass = [
      'et-change-inline',
      baseClass,
      `et-status-${String(change.approval_status || '').toLowerCase()}`,
    ].join(' ');

    if (isRemovalOnly || location.to <= location.from) {
      return;
    }

    decorations.push(
      Decoration.inline(location.from, location.to, {
        class: inlineClass,
        'data-change-id': change.id,
        'data-change-type': semanticType,
        'data-review-status': change.approval_status,
        title: tooltip,
      }),
    );
  });
};

const buildDecorations = (doc: ProseMirrorNode, changes: ElementChange[]): DecorationSet => {
  const decorations: Decoration[] = [];
  const fuzzyPending: ElementChange[] = [];

  changes.forEach((change) => {
    // Prefer deterministic structural rendering; only fall back to fuzzy matching
    // when node path / ordered segments are unavailable or cannot be aligned.
    const handled = applyStructuralDecorations(doc, change, decorations);
    if (!handled) {
      fuzzyPending.push(change);
    }
  });

  if (fuzzyPending.length) {
    applyFuzzyDecorations(doc, fuzzyPending, decorations);
  }

  return DecorationSet.create(doc, decorations);
};

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    enterpriseTrackChanges: {
      setEnterpriseTrackChanges: (changes: ElementChange[]) => ReturnType;
      clearEnterpriseTrackChanges: () => ReturnType;
    };
  }
}

export const setTrackChangesOnEditor = (editor: Editor | null, changes: ElementChange[]) => {
  if (!editor) return;
  editor.commands.setEnterpriseTrackChanges(changes);
};

const asTrackChangesStorage = (editor: Editor): { enterpriseTrackChanges: { changes: ElementChange[] } } => {
  return editor.storage as unknown as { enterpriseTrackChanges: { changes: ElementChange[] } };
};

export const EnterpriseTrackChangesExtension = Extension.create<{ changes: ElementChange[] }>({
  name: 'enterpriseTrackChanges',

  addOptions() {
    return {
      changes: [],
    };
  },

  addStorage() {
    return {
      changes: this.options.changes as ElementChange[],
    };
  },

  addCommands() {
    return {
      setEnterpriseTrackChanges:
        (changes: ElementChange[]) =>
        ({ editor, tr, dispatch }) => {
          asTrackChangesStorage(editor).enterpriseTrackChanges.changes = changes;
          if (dispatch) {
            dispatch(tr.setMeta(pluginKey, { refresh: true }));
          }
          return true;
        },
      clearEnterpriseTrackChanges:
        () =>
        ({ editor, tr, dispatch }) => {
          asTrackChangesStorage(editor).enterpriseTrackChanges.changes = [];
          if (dispatch) {
            dispatch(tr.setMeta(pluginKey, { refresh: true }));
          }
          return true;
        },
    };
  },

  addProseMirrorPlugins() {
    const extension = this;

    return [
      new Plugin<TrackChangesPluginState>({
        key: pluginKey,
        state: {
          init: (_, state) => ({
            decorations: buildDecorations(state.doc, extension.storage.changes as ElementChange[]),
          }),
          apply: (tr, oldState, _oldEditorState, newState) => {
            const meta = tr.getMeta(pluginKey) as { refresh?: boolean } | undefined;
            if (!tr.docChanged && !meta?.refresh) {
              return oldState;
            }
            return {
              decorations: buildDecorations(newState.doc, extension.storage.changes as ElementChange[]),
            };
          },
        },
        props: {
          decorations(state) {
            return pluginKey.getState(state)?.decorations || null;
          },
        },
      }),
    ];
  },
});
