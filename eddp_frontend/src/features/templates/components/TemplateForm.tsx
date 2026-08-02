import { zodResolver } from '@hookform/resolvers/zod';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  FormControlLabel,
  IconButton,
  InputLabel,
  List,
  ListItemButton,
  ListItemText,
  Menu,
  MenuItem,
  Paper,
  Popover,
  Select,
  Stack,
  Tab,
  Tabs,
  Switch,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import AddPhotoAlternateOutlinedIcon from '@mui/icons-material/AddPhotoAlternateOutlined';
import FormatAlignCenterOutlinedIcon from '@mui/icons-material/FormatAlignCenterOutlined';
import FormatAlignJustifyOutlinedIcon from '@mui/icons-material/FormatAlignJustifyOutlined';
import FormatAlignLeftOutlinedIcon from '@mui/icons-material/FormatAlignLeftOutlined';
import FormatAlignRightOutlinedIcon from '@mui/icons-material/FormatAlignRightOutlined';
import FormatBoldOutlinedIcon from '@mui/icons-material/FormatBoldOutlined';
import FormatClearOutlinedIcon from '@mui/icons-material/FormatClearOutlined';
import FormatIndentDecreaseOutlinedIcon from '@mui/icons-material/FormatIndentDecreaseOutlined';
import FormatIndentIncreaseOutlinedIcon from '@mui/icons-material/FormatIndentIncreaseOutlined';
import FormatColorFillOutlinedIcon from '@mui/icons-material/FormatColorFillOutlined';
import FormatColorTextOutlinedIcon from '@mui/icons-material/FormatColorTextOutlined';
import FormatItalicOutlinedIcon from '@mui/icons-material/FormatItalicOutlined';
import FormatListBulletedOutlinedIcon from '@mui/icons-material/FormatListBulletedOutlined';
import FormatListNumberedOutlinedIcon from '@mui/icons-material/FormatListNumberedOutlined';
import FormatStrikethroughOutlinedIcon from '@mui/icons-material/FormatStrikethroughOutlined';
import FormatUnderlinedOutlinedIcon from '@mui/icons-material/FormatUnderlinedOutlined';
import HorizontalRuleOutlinedIcon from '@mui/icons-material/HorizontalRuleOutlined';
import InsertLinkOutlinedIcon from '@mui/icons-material/InsertLinkOutlined';
import RedoOutlinedIcon from '@mui/icons-material/RedoOutlined';
import SaveOutlinedIcon from '@mui/icons-material/SaveOutlined';
import SplitscreenOutlinedIcon from '@mui/icons-material/SplitscreenOutlined';
import SubjectOutlinedIcon from '@mui/icons-material/SubjectOutlined';
import TableRowsOutlinedIcon from '@mui/icons-material/TableRowsOutlined';
import TextFieldsOutlinedIcon from '@mui/icons-material/TextFieldsOutlined';
import TitleOutlinedIcon from '@mui/icons-material/TitleOutlined';
import UndoOutlinedIcon from '@mui/icons-material/UndoOutlined';
import UploadFileOutlinedIcon from '@mui/icons-material/UploadFileOutlined';
import VerticalAlignBottomOutlinedIcon from '@mui/icons-material/VerticalAlignBottomOutlined';
import VerticalAlignTopOutlinedIcon from '@mui/icons-material/VerticalAlignTopOutlined';
import ViewAgendaOutlinedIcon from '@mui/icons-material/ViewAgendaOutlined';
import ZoomInOutlinedIcon from '@mui/icons-material/ZoomInOutlined';
import PrintOutlinedIcon from '@mui/icons-material/PrintOutlined';
import NavigateBeforeOutlinedIcon from '@mui/icons-material/NavigateBeforeOutlined';
import NavigateNextOutlinedIcon from '@mui/icons-material/NavigateNextOutlined';
import DeleteOutlineOutlinedIcon from '@mui/icons-material/DeleteOutlineOutlined';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Underline from '@tiptap/extension-underline';
import Highlight from '@tiptap/extension-highlight';
import { TextStyle } from '@tiptap/extension-text-style';
import Color from '@tiptap/extension-color';
import TextAlign from '@tiptap/extension-text-align';
import Link from '@tiptap/extension-link';
import Image from '@tiptap/extension-image';
import { Table } from '@tiptap/extension-table';
import TableRow from '@tiptap/extension-table-row';
import TableCell from '@tiptap/extension-table-cell';
import TableHeader from '@tiptap/extension-table-header';
import FontFamily from '@tiptap/extension-font-family';
import HorizontalRule from '@tiptap/extension-horizontal-rule';
import Placeholder from '@tiptap/extension-placeholder';
import { Node, mergeAttributes, type JSONContent } from '@tiptap/core';
import { TextSelection } from '@tiptap/pm/state';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Controller, useForm, useWatch } from 'react-hook-form';
import { z } from 'zod';

import { TEMPLATE_TYPE_OPTIONS } from '../../shared/constants';
import { useVariablesByDocument } from '../../variables/hooks/useVariables';
import type { VariableItem } from '../../variables/types';
import type { DocumentItem } from '../../documents/types';
import type { TemplatePayload, TemplateStatus } from '../types';
import { useParseWordDocument } from '../hooks/useTemplates';
import type { ElementChange, ReviewAction } from '../types';
import { EnterpriseTrackChangesExtension, setTrackChangesOnEditor } from './EnterpriseTrackChangesExtension';
import { TrackChangesOverlay } from './TrackChangesOverlay';
import { VariableAutocomplete } from './VariableAutocomplete';
import { EditorSelectionProvider, useEditorSelection, useFormattingState } from '../contexts/EditorSelectionContext';
import {
  autoPaginateDoc,
  extractMarginPxFromLayout,
  normalizeDocForEnterpriseVariables,
  type PMDoc,
} from './editorDocumentTransforms';

const TEMPLATE_STATUS_OPTIONS: readonly TemplateStatus[] = ['DRAFT', 'FOR_REVIEW', 'APPROVED', 'ARCHIVED'] as const;
const TEMPLATE_CATEGORY_OPTIONS = ['LOAN TEMPLATE'] as const;
const PAGE_SIZE_OPTIONS = ['A4', 'A3', 'LETTER', 'LEGAL'] as const;
const ORIENTATION_OPTIONS = ['PORTRAIT', 'LANDSCAPE'] as const;
const FONT_OPTIONS = ['Calibri', 'Cambria', 'Times New Roman', 'Arial', 'Georgia', 'Verdana'] as const;
const FONT_SIZE_OPTIONS = [9, 10, 11, 12, 14, 16, 18, 20, 24, 28, 32, 36];

const PAGE_DIMENSIONS: Record<PageSize, { width: number; height: number }> = {
  A4: { width: 794, height: 1123 },
  A3: { width: 1123, height: 1587 },
  LETTER: { width: 816, height: 1056 },
  LEGAL: { width: 816, height: 1344 },
};

type PageSize = (typeof PAGE_SIZE_OPTIONS)[number];
export type Orientation = (typeof ORIENTATION_OPTIONS)[number];

const normalizePageSize = (value: unknown): PageSize =>
  PAGE_SIZE_OPTIONS.includes(value as PageSize) ? (value as PageSize) : 'A4';

const normalizeOrientation = (value: unknown): Orientation =>
  ORIENTATION_OPTIONS.includes(value as Orientation) ? (value as Orientation) : 'PORTRAIT';

type ProseMirrorDoc = {
  type: 'doc';
  content: Array<Record<string, unknown>>;
} & Record<string, unknown>;

const EMPTY_PROSEMIRROR_DOC: ProseMirrorDoc = {
  type: 'doc',
  content: [{ type: 'paragraph' }],
};

const isProseMirrorDoc = (value: unknown): value is ProseMirrorDoc => {
  if (!value || typeof value !== 'object') {
    return false;
  }

  const record = value as Record<string, unknown>;
  if (record.type !== 'doc') {
    return false;
  }

  const content = record.content;
  if (!Array.isArray(content)) {
    return false;
  }

  return content.some((node) => {
    if (!node || typeof node !== 'object') {
      return false;
    }
    return typeof (node as Record<string, unknown>).type === 'string';
  });
};

const normalizeProseMirrorDoc = (value: unknown): ProseMirrorDoc => {
  if (!isProseMirrorDoc(value)) {
    return EMPTY_PROSEMIRROR_DOC;
  }

  const record = value as Record<string, unknown>;
  const content = (record.content as unknown[])
    .filter((node): node is Record<string, unknown> => {
      if (!node || typeof node !== 'object') {
        return false;
      }
      return typeof (node as Record<string, unknown>).type === 'string';
    });

  if (!content.length) {
    return EMPTY_PROSEMIRROR_DOC;
  }

  return {
    ...(record as ProseMirrorDoc),
    content,
  };
};

const extractProseMirrorDoc = (payload?: TemplatePayload): ProseMirrorDoc => {
  const direct = normalizeProseMirrorDoc(payload?.prosemirror_json);
  if (direct !== EMPTY_PROSEMIRROR_DOC || isProseMirrorDoc(payload?.prosemirror_json)) {
    return direct;
  }

  return EMPTY_PROSEMIRROR_DOC;
};

const createEnterpriseVariableNode = (name: string, className: string) => Node.create({
  name,
  group: 'inline',
  inline: true,
  atom: true,
  selectable: true,
  draggable: true,
  addAttributes() {
    return {
      field: {
        default: '',
        parseHTML: (element) => (element as HTMLElement).getAttribute('data-field') || '',
      },
      label: {
        default: '',
        parseHTML: (element) => (element as HTMLElement).getAttribute('data-label') || '',
      },
      category: {
        default: '',
        parseHTML: (element) => (element as HTMLElement).getAttribute('data-category') || '',
      },
      normalized: {
        default: '',
        parseHTML: (element) => (element as HTMLElement).getAttribute('data-normalized') || '',
      },
      source_format: {
        default: '',
        parseHTML: (element) => (element as HTMLElement).getAttribute('data-source-format') || '',
      },
    };
  },
  parseHTML() {
    if (name === 'variableChip') {
      return [{ tag: 'span.variable-chip[data-field]' }, { tag: 'span[data-field]' }];
    }
    return [{ tag: `span.${className}[data-field]` }];
  },
  renderHTML({ HTMLAttributes }) {
    const {
      field = '',
      label = '',
      category = '',
      normalized = '',
      source_format = '',
      ...rest
    } = HTMLAttributes;
    const normalizedField = typeof field === 'string' ? field.trim() : '';
    const normalizedLabel = typeof label === 'string' ? label.trim() : '';
    const fallbackToken = normalizedLabel
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '');
    const token = normalizedField || fallbackToken || 'variable';
    const normalizedValue = typeof normalized === 'string' && normalized.trim() ? normalized.trim() : `<${token}>`;
    return [
      'span',
      mergeAttributes(
        {
          'data-field': field,
          'data-label': label || field,
          'data-category': category,
          'data-normalized': normalizedValue,
          'data-source-format': source_format,
          class: `variable-chip ${className}`,
          contenteditable: 'false',
        },
        rest,
      ),
      normalizedValue,
    ];
  },

  // ---- ADDED: plain-text serialization for atom leaf node ------------------
  // Makes the chip copyable as "<loan_tenure>" (Ctrl+C / clipboard) and ensures
  // editor.getText() and backend diff extraction include the token so nearby
  // edits (e.g. removing " Months") are detected and rendered correctly.
  renderText({ node }) {
    const attrs = (node.attrs ?? {}) as Record<string, unknown>;
    const field = typeof attrs.field === 'string' ? attrs.field.trim() : '';
    const label = typeof attrs.label === 'string' ? attrs.label.trim() : '';
    const normalized = typeof attrs.normalized === 'string' ? attrs.normalized.trim() : '';
    const fallbackToken = label
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '');
    const token = field || fallbackToken || 'variable';
    return normalized || `<${token}>`;
  },
  // -------------------------------------------------------------------------
});

const VariableChipNode = createEnterpriseVariableNode('variableChip', 'variable-chip-simple');
const DynamicTableVariableNode = createEnterpriseVariableNode('dynamicTableVariable', 'variable-chip-dynamic-table');
const SignatureVariableNode = createEnterpriseVariableNode('signatureVariable', 'variable-chip-signature');
const ImagePlaceholderVariableNode = createEnterpriseVariableNode('imagePlaceholderVariable', 'variable-chip-image');
const EnterpriseTable = Table.extend({
  draggable: true,
}).configure({
  resizable: true,
  lastColumnResizable: true,
});
const PageBreakNode = Node.create({
  name: 'pageBreak',
  group: 'block',
  atom: true,
  selectable: false,
  draggable: false,
  addAttributes() {
    return {
      auto: {
        default: false,
      },
      source: {
        default: 'manual',
      },
    };
  },
  parseHTML() {
    return [{ tag: 'hr[data-page-break="true"]' }];
  },
  renderHTML({ HTMLAttributes }) {
    const auto = Boolean(HTMLAttributes.auto);
    return [
      'hr',
      mergeAttributes(
        {
          'data-page-break': 'true',
          'data-page-break-mode': auto ? 'auto' : 'manual',
          class: auto ? 'page-break page-break-auto' : 'page-break page-break-manual',
        },
        HTMLAttributes,
      ),
    ];
  },
});

const flattenLayoutText = (nodes: Record<string, unknown>[] | undefined): string => {
  if (!nodes || !Array.isArray(nodes)) {
    return '';
  }

  const walk = (node: Record<string, unknown>): string => {
    if (typeof node.text === 'string') {
      return node.text;
    }
    const content = Array.isArray(node.content) ? (node.content as Record<string, unknown>[]) : [];
    return content.map(walk).join(' ');
  };

  return nodes.map(walk).join(' ').replace(/\s+/g, ' ').trim();
};

const getPageBreakPositions = (currentEditor: NonNullable<ReturnType<typeof useEditor>>): number[] => {
  const breaks: number[] = [];
  currentEditor.state.doc.descendants((node, pos) => {
    if (node.type.name === 'pageBreak') {
      breaks.push(pos);
    }
  });
  return breaks.sort((a, b) => a - b);
};

const setEditorContent = (
  currentEditor: NonNullable<ReturnType<typeof useEditor>>,
  doc: PMDoc,
  emitUpdate = true,
) => {
  currentEditor.commands.setContent(doc as JSONContent, { emitUpdate });
};

const templateSchema = z.object({
  code: z.string().min(3, 'Code must be at least 3 characters.'),
  name: z.string().min(2, 'Name must be at least 2 characters.'),
  description: z.string(),
  category: z.enum(TEMPLATE_CATEGORY_OPTIONS),
  document_id: z.string().uuid('Document ID must be a valid UUID.'),
  template_type: z.enum(TEMPLATE_TYPE_OPTIONS),
  content_type: z.string().min(2, 'Content type is required.'),
  is_default: z.boolean(),
  status: z.enum(TEMPLATE_STATUS_OPTIONS),
});

type FormValues = z.infer<typeof templateSchema>;

type Props = {
  initialValue?: TemplatePayload;
  existingCodes?: string[];
  documents?: DocumentItem[];
  templateStatus?: string;
  currentVersion?: number;
  versionCount?: number;
  readOnly?: boolean;
  reviewChanges?: ElementChange[];
  versionLabel?: string;
  documentId?: string;
  onReviewChange?: (changeId: string, action: ReviewAction, comment?: string) => void;
  reviewActionsDisabled?: boolean;
  onSubmit: (payload: TemplatePayload) => Promise<void>;
  onSendForReview?: (payload: TemplatePayload) => Promise<void> | void;
  onApprove?: () => void;
};

const defaultValue: TemplatePayload = {
  code: '',
  name: '',
  description: '',
  category: 'LOAN TEMPLATE',
  document_id: '',
  template_type: 'STATIC',
  content_type: 'application/json',
  is_default: false,
  status: 'DRAFT',
};

const toTemplateFormValues = (initialValue?: TemplatePayload): FormValues => ({
  code: initialValue?.code ?? defaultValue.code,
  name: initialValue?.name ?? defaultValue.name,
  description: initialValue?.description ?? defaultValue.description,
  category: initialValue?.category === 'LOAN TEMPLATE' ? 'LOAN TEMPLATE' : 'LOAN TEMPLATE',
  document_id: initialValue?.document_id ?? defaultValue.document_id,
  template_type:
    initialValue?.template_type === 'STATIC' ||
    initialValue?.template_type === 'DYNAMIC' ||
    initialValue?.template_type === 'COMPOSITE'
      ? initialValue.template_type
      : defaultValue.template_type,
  content_type: initialValue?.content_type ?? defaultValue.content_type,
  is_default: initialValue?.is_default ?? defaultValue.is_default,
  status:
    initialValue?.status === 'DRAFT' ||
    initialValue?.status === 'FOR_REVIEW' ||
    initialValue?.status === 'APPROVED' ||
    initialValue?.status === 'ARCHIVED'
      ? initialValue.status
      : defaultValue.status,
});

const normalizeNameToken = (value: string): string =>
  value
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .replace(/_+TEMPLATE$/, '')
    .slice(0, 80);

const generateTemplateCode = (name: string, existingCodes: string[]): string => {
  const token = normalizeNameToken(name);
  if (!token) return '';

  const prefix = `DOC_${token}_TEMPLATE_`;
  const matcher = new RegExp(`^${prefix.replace(/[.*+?^${}()|[\\]\\]/g, '\\\\$&')}(\\d{6})$`);
  const usedSequences = new Set<number>();

  for (const existingCode of existingCodes) {
    const match = existingCode.match(matcher);
    if (match) usedSequences.add(Number(match[1]));
  }

  let nextValue = 1;
  while (usedSequences.has(nextValue) && nextValue <= 999999) {
    nextValue += 1;
  }

  return `${prefix}${String(nextValue).padStart(6, '0')}`;
};

const mapVariableCategory = (variable: VariableItem): string => {
  const source = `${variable.group?.name ?? ''} ${variable.name} ${variable.display_name}`.toLowerCase();
  if (source.includes('co-app')) return 'Co-Applicant';
  if (source.includes('loan')) return 'Loan';
  if (source.includes('property')) return 'Property';
  if (source.includes('branch')) return 'Branch';
  if (source.includes('emi')) return 'EMI';
  if (source.includes('interest') || source.includes('roi')) return 'Interest';
  if (source.includes('disburse')) return 'Disbursement';
  if (source.includes('technical')) return 'Technical';
  if (source.includes('legal')) return 'Legal';
  if (source.includes('insurance')) return 'Insurance';
  if (source.includes('customer')) return 'Customer';
  if (source.includes('applicant')) return 'Applicant';
  return 'Applicant';
};

const ribbonButtonSx = {
  border: '1px solid #d1d5db',
  borderRadius: 1,
} as const;

type TableContextMenuState = {
  mouseX: number;
  mouseY: number;
  open: boolean;
};

type TablePropertiesState = {
  widthPreset: 'AUTO' | '100' | '75' | '50' | 'CUSTOM';
  preferredWidthUnit: '%' | 'px';
  preferredWidth: string;
  columnWidth: string;
  rowHeight: string;
  minimumRowHeight: string;
  borderColor: string;
  borderWidth: string;
  cellBackground: string;
  horizontalAlign: 'left' | 'center' | 'right' | 'justify';
  verticalAlign: 'top' | 'middle' | 'bottom';
  autoFit: 'auto' | 'fixed';
  repeatHeaderRow: boolean;
  allowRowBreak: boolean;
  cellPadding: string;
  cellSpacing: string;
  tableMarginTop: string;
  tableMarginBottom: string;
  tableMarginLeft: string;
  tableMarginRight: string;
  collectionName: string;
  repeatDirection: 'vertical' | 'horizontal';
  maximumRows: string;
  footerRow: boolean;
};

const defaultTableProperties: TablePropertiesState = {
  widthPreset: '100',
  preferredWidthUnit: '%',
  preferredWidth: '100',
  columnWidth: '',
  rowHeight: '',
  minimumRowHeight: '',
  borderColor: '#cbd5e1',
  borderWidth: '1',
  cellBackground: '#ffffff',
  horizontalAlign: 'left',
  verticalAlign: 'top',
  autoFit: 'fixed',
  repeatHeaderRow: true,
  allowRowBreak: true,
  cellPadding: '6',
  cellSpacing: '0',
  tableMarginTop: '0',
  tableMarginBottom: '0',
  tableMarginLeft: '0',
  tableMarginRight: '0',
  collectionName: '',
  repeatDirection: 'vertical',
  maximumRows: '',
  footerRow: false,
};

const extractNumericText = (value: unknown): string => {
  if (typeof value !== 'string' || !value.trim()) {
    return '';
  }
  const match = value.match(/-?\d+(?:\.\d+)?/);
  return match ? match[0] : '';
};

const extractBorderWidth = (border: string | undefined): string => {
  if (!border) {
    return '';
  }
  const match = border.match(/(\d+(?:\.\d+)?)px/i);
  return match ? match[1] : '';
};

const extractBorderColor = (border: string | undefined): string => {
  if (!border) {
    return '';
  }
  const hexMatch = border.match(/#[0-9a-fA-F]{3,8}/);
  if (hexMatch) {
    return hexMatch[0];
  }
  return '';
};

const expandCssBoxShorthand = (value: string | undefined): {
  top?: string;
  right?: string;
  bottom?: string;
  left?: string;
} => {
  if (!value || !value.trim()) {
    return {};
  }

  const parts = value.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) {
    return {};
  }

  if (parts.length === 1) {
    return { top: parts[0], right: parts[0], bottom: parts[0], left: parts[0] };
  }

  if (parts.length === 2) {
    return { top: parts[0], right: parts[1], bottom: parts[0], left: parts[1] };
  }

  if (parts.length === 3) {
    return { top: parts[0], right: parts[1], bottom: parts[2], left: parts[1] };
  }

  return { top: parts[0], right: parts[1], bottom: parts[2], left: parts[3] };
};

const parseStyle = (styleText: unknown): Record<string, string> => {
  if (typeof styleText !== 'string' || !styleText.trim()) {
    return {};
  }

  return styleText
    .split(';')
    .map((item) => item.trim())
    .filter(Boolean)
    .reduce<Record<string, string>>((acc, current) => {
      const dividerIndex = current.indexOf(':');
      if (dividerIndex <= 0) {
        return acc;
      }
      const key = current.slice(0, dividerIndex).trim().toLowerCase();
      const value = current.slice(dividerIndex + 1).trim();
      if (!key || !value) {
        return acc;
      }
      acc[key] = value;
      return acc;
    }, {});
};

const stringifyStyle = (styleMap: Record<string, string>): string =>
  Object.entries(styleMap)
    .map(([key, value]) => `${key}: ${value}`)
    .join('; ');

const upsertStyle = (existingStyle: unknown, updates: Record<string, string>): string => {
  const current = parseStyle(existingStyle);
  const merged = {
    ...current,
    ...updates,
  };
  return stringifyStyle(merged);
};

const findClosestTableElement = (target: EventTarget | null): HTMLTableElement | null => {
  if (!target || !(target instanceof globalThis.Node)) {
    return null;
  }

  let current: globalThis.Node | null = target;
  while (current) {
    if (current instanceof HTMLTableElement) {
      return current;
    }
    current = current.parentNode;
  }

  return null;
};

const dynamicTableNode = (rows: Array<Array<string>>): JSONContent => ({
  type: 'table',
  content: rows.map((row, rowIndex) => ({
    type: 'tableRow',
    content: row.map((cell) => ({
      type: rowIndex === 0 ? 'tableHeader' : 'tableCell',
      content: [
        {
          type: 'paragraph',
          content: [{ type: 'text', text: cell }],
        },
      ],
    })),
  })),
});

const ENTERPRISE_DYNAMIC_TABLES: Record<string, JSONContent> = {
  ADDRESS_TABLE: dynamicTableNode([
    ['Address Line 1', 'Address Line 2', 'City', 'Postal Code'],
    ['<ADDRESS_LINE_1>', '<ADDRESS_LINE_2>', '<CITY>', '<POSTAL_CODE>'],
  ]),
  SIGNATURE_TABLE: dynamicTableNode([
    ['Name', 'Signature', 'Date'],
    ['<SIGNATORY_NAME>', '<SIGNATURE>', '<SIGNATURE_DATE>'],
  ]),
  AMORTIZATION_TABLE: dynamicTableNode([
    ['Installment', 'Principal', 'Interest', 'Balance'],
    ['<EMI_NO>', '<PRINCIPAL_COMPONENT>', '<INTEREST_COMPONENT>', '<OUTSTANDING_BALANCE>'],
  ]),
  PAYMENT_SCHEDULE: dynamicTableNode([
    ['Due Date', 'Amount', 'Status'],
    ['<DUE_DATE>', '<INSTALLMENT_AMOUNT>', '<PAYMENT_STATUS>'],
  ]),
  CUSTOMER_TABLE: dynamicTableNode([
    ['Customer ID', 'Customer Name', 'Contact'],
    ['<CUSTOMER_ID>', '<CUSTOMER_NAME>', '<CUSTOMER_CONTACT>'],
  ]),
};

/**
 * SelectionStatusBar - Demonstrates EditorSelectionContext integration
 * Shows real-time selection state from ProseMirror
 */
function SelectionStatusBar() {
  const { contentType, hasSelection, selectionMode } = useEditorSelection();
  const { bold, italic, underline } = useFormattingState();

  if (!hasSelection) {
    return null;
  }

  return (
    <Box
      sx={{
        position: 'absolute',
        bottom: 40,
        left: 12,
        right: 12,
        px: 1.5,
        py: 0.75,
        bgcolor: 'rgba(59, 130, 246, 0.95)',
        color: 'white',
        borderRadius: 1,
        display: 'flex',
        alignItems: 'center',
        gap: 2,
        fontSize: '0.75rem',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        zIndex: 10,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.8)', fontWeight: 600 }}>
          Selection:
        </Typography>
        <Typography variant="caption" sx={{ color: 'white', fontWeight: 500 }}>
          {contentType} ({selectionMode})
        </Typography>
      </Box>
      {(bold || italic || underline) && (
        <>
          <Divider orientation="vertical" flexItem sx={{ borderColor: 'rgba(255,255,255,0.3)' }} />
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            {bold && (
              <Chip
                label="Bold"
                size="small"
                sx={{
                  height: 20,
                  fontSize: '0.65rem',
                  bgcolor: 'rgba(255,255,255,0.2)',
                  color: 'white',
                }}
              />
            )}
            {italic && (
              <Chip
                label="Italic"
                size="small"
                sx={{
                  height: 20,
                  fontSize: '0.65rem',
                  bgcolor: 'rgba(255,255,255,0.2)',
                  color: 'white',
                }}
              />
            )}
            {underline && (
              <Chip
                label="Underline"
                size="small"
                sx={{
                  height: 20,
                  fontSize: '0.65rem',
                  bgcolor: 'rgba(255,255,255,0.2)',
                  color: 'white',
                }}
              />
            )}
          </Box>
        </>
      )}
      <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.65rem' }}>
          ✓ EditorSelectionContext Active
        </Typography>
      </Box>
    </Box>
  );
}

export function TemplateForm({
  initialValue,
  existingCodes = [],
  documents = [],
  templateStatus,
  currentVersion,
  versionCount,
  readOnly = false,
  reviewChanges = [],
  versionLabel = '',
  documentId = '',
  onReviewChange,
  reviewActionsDisabled = false,
  onSubmit,
  onSendForReview,
  onApprove,
}: Props) {
  const {
    control,
    handleSubmit,
    register,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(templateSchema),
    defaultValues: toTemplateFormValues(initialValue),
  });

  const values = useWatch({ control });
  const variablesQuery = useVariablesByDocument(values.document_id);
  const parseWordMutation = useParseWordDocument();
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const [pageSize, setPageSize] = useState<PageSize>(normalizePageSize(initialValue?.page_size));
  const [orientation, setOrientation] = useState<Orientation>(normalizeOrientation(initialValue?.page_orientation));
  const [marginPx, setMarginPx] = useState(24);
  const [zoomPercent, setZoomPercent] = useState(100);
  const [activePage, setActivePage] = useState(1);
  const [layoutHeaderText, setLayoutHeaderText] = useState('');
  const [layoutFooterText, setLayoutFooterText] = useState('');
  const [fontFamily, setFontFamily] = useState<(typeof FONT_OPTIONS)[number]>('Calibri');
  const [fontSize, setFontSize] = useState(12);
  const [designTab, setDesignTab] = useState<'elements' | 'fields'>('elements');
  const autocompleteAnchorRef = useRef<HTMLElement | null>(null);
  const [autocompleteAnchorEl, setAutocompleteAnchorEl] = useState<HTMLElement | null>(null);
  const [autocompleteSearchText, setAutocompleteSearchText] = useState('');
  const [tableContextMenu, setTableContextMenu] = useState<TableContextMenuState>({ mouseX: 0, mouseY: 0, open: false });
  const [insertTableMenuAnchor, setInsertTableMenuAnchor] = useState<HTMLElement | null>(null);
  const [insertTableDialogOpen, setInsertTableDialogOpen] = useState(false);
  const [insertTableRows, setInsertTableRows] = useState(3);
  const [insertTableCols, setInsertTableCols] = useState(4);
  const [hoverRows, setHoverRows] = useState(0);
  const [hoverCols, setHoverCols] = useState(0);
  const [tablePropertiesOpen, setTablePropertiesOpen] = useState(false);
  const [tableProperties, setTableProperties] = useState<TablePropertiesState>(defaultTableProperties);

  const initialProsemirrorDoc = useMemo(
    () => extractProseMirrorDoc(initialValue),
    [initialValue?.prosemirror_json],
  );
  
  const closeVariableAutocomplete = useCallback(() => {
    const anchor = autocompleteAnchorRef.current;
    if (anchor && document.body.contains(anchor)) {
      document.body.removeChild(anchor);
    }
    autocompleteAnchorRef.current = null;
    setAutocompleteAnchorEl(null);
    setAutocompleteSearchText('');
  }, []);

  const syncVariableAutocomplete = useCallback((currentEditor: NonNullable<ReturnType<typeof useEditor>>) => {
    if (readOnly) {
      closeVariableAutocomplete();
      return;
    }

    const cursorPos = currentEditor.state.selection.from;
    const start = Math.max(0, cursorPos - 80);
    const textBeforeCursor = currentEditor.state.doc.textBetween(start, cursorPos, '\n', '\n');
    const match = textBeforeCursor.match(/\$([A-Za-z0-9_]*)$/);

    if (!match) {
      closeVariableAutocomplete();
      return;
    }

    const search = match[1] ?? '';
    const coords = currentEditor.view.coordsAtPos(cursorPos);

    let anchor = autocompleteAnchorRef.current;
    if (!anchor) {
      anchor = document.createElement('span');
      anchor.style.position = 'fixed';
      anchor.style.width = '1px';
      anchor.style.height = '1px';
      anchor.style.pointerEvents = 'none';
      anchor.style.zIndex = '10001';
      document.body.appendChild(anchor);
      autocompleteAnchorRef.current = anchor;
    }

    anchor.style.left = `${coords.left}px`;
    anchor.style.top = `${coords.bottom}px`;

    setAutocompleteSearchText(search);
    setAutocompleteAnchorEl(anchor);
  }, [closeVariableAutocomplete, readOnly]);

  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      Highlight,
      TextStyle,
      Color,
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      Link.configure({ openOnClick: false, autolink: true }),
      Image.configure({ inline: true, allowBase64: true }),
      EnterpriseTable,
      TableRow,
      TableHeader,
      TableCell,
      FontFamily,
      HorizontalRule,
      PageBreakNode,
      Placeholder.configure({ placeholder: 'Type your document here...' }),
      VariableChipNode,
      DynamicTableVariableNode,
      SignatureVariableNode,
      ImagePlaceholderVariableNode,
      EnterpriseTrackChangesExtension.configure({ changes: reviewChanges }),
    ],
    content: initialProsemirrorDoc,
    onUpdate: ({ editor: current }) => {
      syncVariableAutocomplete(current);
    },
    editorProps: {
      attributes: {
        class: 'enterprise-doc-editor',
      },
      handleKeyDown: (_view, event) => {
        if (!editor || readOnly) {
          return false;
        }

        const isCtrl = event.ctrlKey || event.metaKey;
        if (isCtrl && event.key.toLowerCase() === 'f') {
          event.preventDefault();
          const search = window.prompt('Find text');
          if (!search) {
            return true;
          }
          const content = editor.state.doc.textContent;
          const idx = content.toLowerCase().indexOf(search.toLowerCase());
          if (idx >= 0) {
            editor.commands.setTextSelection({ from: Math.max(1, idx + 1), to: Math.max(2, idx + search.length + 1) });
          }
          return true;
        }

        if (isCtrl && event.key.toLowerCase() === 'h') {
          event.preventDefault();
          const findTerm = window.prompt('Find');
          if (!findTerm) {
            return true;
          }
          const replaceTerm = window.prompt('Replace with') ?? '';
          const currentJson = editor.getJSON();
          const serialized = JSON.stringify(currentJson);
          const escaped = findTerm.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
          const replaced = serialized.replace(new RegExp(escaped, 'gi'), replaceTerm);
          try {
            editor.commands.setContent(JSON.parse(replaced));
          } catch {
            // Keep editor state unchanged if replacement creates invalid JSON.
          }
          return true;
        }

        if (isTableSelection && event.key === 'Delete' && event.shiftKey) {
          event.preventDefault();
          editor.chain().focus().deleteRow().run();
          return true;
        }

        if (isTableSelection && event.key === 'Backspace' && event.shiftKey) {
          event.preventDefault();
          editor.chain().focus().deleteColumn().run();
          return true;
        }

        return false;
      },
      handleDOMEvents: {
        contextmenu: (_view, event) => {
          if (!editor || readOnly) {
            return false;
          }

          const table = findClosestTableElement(event.target);
          if (!table) {
            return false;
          }

          event.preventDefault();
          const target = event.target as HTMLElement | null;
          if (target) {
            const coords = editor.view.posAtDOM(target, 0);
            editor.chain().focus().setTextSelection(coords).run();
          }
          setTableContextMenu({ mouseX: event.clientX + 2, mouseY: event.clientY - 6, open: true });
          return true;
        },
      },
      handleDrop: (_view, event) => {
        const variableRaw = event.dataTransfer?.getData('application/eddp-variable');
        if (!variableRaw || !editor) return false;

        try {
          const variable = JSON.parse(variableRaw) as { token: string; label: string };
          const coords = editor.view.posAtCoords({ left: event.clientX, top: event.clientY });
          const content = {
            type: 'variableChip',
            attrs: {
              field: variable.token,
              label: variable.label,
            },
          };

          if (coords) {
            editor.chain().focus().insertContentAt(coords.pos, content).run();
          } else {
            editor.chain().focus().insertContent(content).run();
          }
          return true;
        } catch {
          return false;
        }
      },
    },
  });

  useEffect(() => {
    if (initialValue?.code || !values.name) return;
    const nextCode = generateTemplateCode(values.name, existingCodes);
    if (nextCode) {
      setValue('code', nextCode, { shouldValidate: true, shouldDirty: false });
    }
  }, [existingCodes, initialValue, setValue, values.name]);

  useEffect(() => {
    if (!editor) return;
    editor.setEditable(!readOnly);
  }, [editor, readOnly]);

  useEffect(() => {
    setTrackChangesOnEditor(editor, reviewChanges);
  }, [editor, reviewChanges]);

  useEffect(() => () => {
    closeVariableAutocomplete();
  }, [closeVariableAutocomplete]);

  useEffect(() => {
    if (!editor) {
      return;
    }

    const handleSelectionChange = () => {
      const cursorPos = editor.state.selection.from;
      const positions = getPageBreakPositions(editor);
      let page = 1;
      for (const pos of positions) {
        if (cursorPos > pos) {
          page += 1;
        }
      }
      setActivePage(page);
    };

    editor.on('selectionUpdate', handleSelectionChange);
    editor.on('update', handleSelectionChange);
    handleSelectionChange();

    return () => {
      editor.off('selectionUpdate', handleSelectionChange);
      editor.off('update', handleSelectionChange);
    };
  }, [editor]);

  const syncSelectedTableHighlight = useCallback(() => {
    if (!editor) {
      return;
    }

    const editorRoot = editor.view.dom as HTMLElement;
    editorRoot.querySelectorAll('table.eddp-selected-table').forEach((tableElement) => {
      tableElement.classList.remove('eddp-selected-table');
    });

    const hasTableSelection = Boolean(
      editor.isActive('table') ||
      editor.isActive('tableRow') ||
      editor.isActive('tableCell') ||
      editor.isActive('tableHeader'),
    );

    if (!hasTableSelection) {
      return;
    }

    const from = editor.state.selection.from;
    const domAtPos = editor.view.domAtPos(from);
    const table = findClosestTableElement(domAtPos.node);
    if (table) {
      table.classList.add('eddp-selected-table');
    }
  }, [editor]);

  useEffect(() => {
    if (!editor) {
      return;
    }

    const handleUpdate = () => {
      syncSelectedTableHighlight();
    };

    editor.on('selectionUpdate', handleUpdate);
    editor.on('update', handleUpdate);
    handleUpdate();

    return () => {
      editor.off('selectionUpdate', handleUpdate);
      editor.off('update', handleUpdate);
      const editorRoot = editor.view.dom as HTMLElement;
      editorRoot.querySelectorAll('table.eddp-selected-table').forEach((tableElement) => {
        tableElement.classList.remove('eddp-selected-table');
      });
    };
  }, [editor, syncSelectedTableHighlight]);

  const closeTableContextMenu = useCallback(() => {
    setTableContextMenu({ mouseX: 0, mouseY: 0, open: false });
  }, []);

  const handleAutocompleteSelect = useCallback((variableName: string) => {
    if (!editor) {
      closeVariableAutocomplete();
      return;
    }

    const cursorPos = editor.state.selection.from;
    const deleteFrom = Math.max(0, cursorPos - (autocompleteSearchText.length + 1));
    const variableLabel = (variablesQuery.data ?? []).find((item) => item.name === variableName)?.display_name
      ?? variableName.replace(/_/g, ' ').replace(/\b\w/g, (s) => s.toUpperCase());

    editor
      .chain()
      .focus()
      .deleteRange({ from: deleteFrom, to: cursorPos })
      .insertContent({
        type: 'variableChip',
        attrs: {
          field: variableName,
          label: variableLabel,
        },
      })
      .run();

    closeVariableAutocomplete();
  }, [autocompleteSearchText.length, closeVariableAutocomplete, editor, variablesQuery.data]);

  const groupedVariables = useMemo(() => {
    const groups = new Map<string, Array<{ token: string; label: string; description: string }>>();
    (variablesQuery.data ?? []).forEach((variable) => {
      const category = mapVariableCategory(variable);
      const entry = {
        token: variable.name,
        label: variable.display_name || variable.name,
        description: variable.description,
      };
      const current = groups.get(category) ?? [];
      current.push(entry);
      groups.set(category, current);
    });

    const categoryOrder = [
      'Applicant',
      'Co-Applicant',
      'Loan',
      'Property',
      'Customer',
      'Branch',
      'EMI',
      'Interest',
      'Disbursement',
      'Technical',
      'Legal',
      'Insurance',
    ];

    return categoryOrder
      .map((name) => ({ name, items: groups.get(name) ?? [] }))
      .filter((group) => group.items.length > 0);
  }, [variablesQuery.data]);

  const pageDimension = useMemo(() => {
    const base = PAGE_DIMENSIONS[pageSize];
    return orientation === 'LANDSCAPE' ? { width: base.height, height: base.width } : base;
  }, [orientation, pageSize]);

  const breakPositions = useMemo(() => {
    if (!editor) {
      return [] as number[];
    }
    return getPageBreakPositions(editor);
  }, [editor, editor?.state.doc]);

  const totalPages = Math.max(1, breakPositions.length + 1);
  const isTableSelection = Boolean(
    editor?.isActive('table') || editor?.isActive('tableRow') || editor?.isActive('tableCell') || editor?.isActive('tableHeader'),
  );

  const runTableCommand = useCallback((command: (currentEditor: NonNullable<ReturnType<typeof useEditor>>) => boolean) => {
    if (readOnly || !editor) {
      return;
    }

    const focused = editor.chain().focus().run();
    if (!focused) {
      return;
    }

    command(editor);
  }, [editor, readOnly]);

  const setCellStyle = useCallback((updates: Record<string, string>) => {
    if (readOnly || !editor || !isTableSelection) {
      return;
    }

    const attrs = editor.getAttributes('tableCell');
    const currentStyle = attrs.style as string | undefined;
    const nextStyle = upsertStyle(currentStyle, updates);
    editor.chain().focus().setCellAttribute('style', nextStyle).run();
  }, [editor, isTableSelection, readOnly]);

  const insertEnterpriseTable = useCallback((tableKey: keyof typeof ENTERPRISE_DYNAMIC_TABLES) => {
    if (readOnly || !editor) {
      return;
    }

    const templateNode = ENTERPRISE_DYNAMIC_TABLES[tableKey];
    if (!templateNode) {
      return;
    }

    editor.chain().focus().insertContent(templateNode).run();
  }, [editor, readOnly]);

  const insertSignatureTable = useCallback(() => {
    insertEnterpriseTable('SIGNATURE_TABLE');
  }, [insertEnterpriseTable]);

  const applyTableProperties = useCallback((nextTableProperties: TablePropertiesState = tableProperties) => {
    if (readOnly || !editor || !isTableSelection) {
      return;
    }

    const borderWidth = Number(nextTableProperties.borderWidth || 1);
    const safeBorderWidth = Number.isFinite(borderWidth) ? Math.max(0, borderWidth) : 1;
    const preferredWidth = Number(nextTableProperties.preferredWidth || (nextTableProperties.preferredWidthUnit === '%' ? 100 : 240));
    const safePreferredWidth = Number.isFinite(preferredWidth) ? Math.max(0, preferredWidth) : 100;
    const padding = Number(nextTableProperties.cellPadding || 6);
    const safePadding = Number.isFinite(padding) ? Math.max(0, padding) : 6;
    const rowHeight = Number(nextTableProperties.rowHeight || 0);
    const minimumRowHeight = Number(nextTableProperties.minimumRowHeight || 0);

    let widthCss = '100%';
    if (nextTableProperties.widthPreset === 'AUTO') {
      widthCss = 'auto';
    } else if (nextTableProperties.widthPreset !== 'CUSTOM') {
      widthCss = `${nextTableProperties.widthPreset}%`;
    } else if (nextTableProperties.preferredWidthUnit === 'px') {
      widthCss = `${Math.max(60, safePreferredWidth)}px`;
    } else {
      widthCss = `${Math.max(10, Math.min(100, safePreferredWidth))}%`;
    }

    setCellStyle({
      'background-color': nextTableProperties.cellBackground || '#ffffff',
      border: `${safeBorderWidth}px solid ${nextTableProperties.borderColor || '#cbd5e1'}`,
      'vertical-align': nextTableProperties.verticalAlign,
      'text-align': nextTableProperties.horizontalAlign,
      width: nextTableProperties.columnWidth ? `${Number(nextTableProperties.columnWidth)}px` : 'auto',
      height: nextTableProperties.rowHeight && Number.isFinite(rowHeight) ? `${Math.max(0, rowHeight)}px` : 'auto',
      'min-height': nextTableProperties.minimumRowHeight && Number.isFinite(minimumRowHeight)
        ? `${Math.max(0, minimumRowHeight)}px`
        : 'auto',
      padding: `${safePadding}px`,
    });

    editor.chain().focus().setCellAttribute('colwidth', nextTableProperties.columnWidth
      ? [Math.max(16, Number(nextTableProperties.columnWidth))]
      : null).run();
    editor.chain().focus().setCellAttribute('rowspan', 1).run();
    editor.chain().focus().setCellAttribute('colspan', 1).run();

    const tableAttrs = editor.getAttributes('table');
    const marginMode =
      nextTableProperties.horizontalAlign === 'center'
        ? '0 auto'
        : nextTableProperties.horizontalAlign === 'right'
          ? '0 0 0 auto'
          : '0 auto 0 0';
    const spacing = Number(nextTableProperties.cellSpacing || 0);
    const safeSpacing = Number.isFinite(spacing) ? Math.max(0, spacing) : 0;
    const tableMarginTop = Number(nextTableProperties.tableMarginTop || 0);
    const tableMarginBottom = Number(nextTableProperties.tableMarginBottom || 0);
    const tableMarginLeft = Number(nextTableProperties.tableMarginLeft || 0);
    const tableMarginRight = Number(nextTableProperties.tableMarginRight || 0);
    const safeTableMarginTop = Number.isFinite(tableMarginTop) ? Math.max(0, tableMarginTop) : 0;
    const safeTableMarginBottom = Number.isFinite(tableMarginBottom) ? Math.max(0, tableMarginBottom) : 0;
    const safeTableMarginLeft = Number.isFinite(tableMarginLeft) ? Math.max(0, tableMarginLeft) : 0;
    const safeTableMarginRight = Number.isFinite(tableMarginRight) ? Math.max(0, tableMarginRight) : 0;

    const marginLeftCss =
      nextTableProperties.horizontalAlign === 'center'
        ? 'auto'
        : nextTableProperties.horizontalAlign === 'right'
          ? 'auto'
          : `${safeTableMarginLeft}px`;
    const marginRightCss =
      nextTableProperties.horizontalAlign === 'center'
        ? 'auto'
        : nextTableProperties.horizontalAlign === 'right'
          ? `${safeTableMarginRight}px`
          : 'auto';

    const tableStyle = upsertStyle(tableAttrs.style, {
      width: widthCss,
      'table-layout': nextTableProperties.autoFit === 'fixed' ? 'fixed' : 'auto',
      margin: marginMode,
      'margin-top': `${safeTableMarginTop}px`,
      'margin-bottom': `${safeTableMarginBottom}px`,
      'margin-left': marginLeftCss,
      'margin-right': marginRightCss,
      'border-spacing': `${safeSpacing}px`,
      'border-collapse': safeSpacing > 0 ? 'separate' : 'collapse',
      'break-inside': nextTableProperties.allowRowBreak ? 'auto' : 'avoid',
    });
    editor.chain().focus().updateAttributes('table', { style: tableStyle }).run();

    const hasHeaderRow = editor.isActive('tableHeader');
    if (nextTableProperties.repeatHeaderRow !== hasHeaderRow) {
      editor.chain().focus().toggleHeaderRow().run();
    }
  }, [editor, isTableSelection, readOnly, setCellStyle, tableProperties]);

  const syncTablePropertiesFromSelection = useCallback(() => {
    if (!editor || !isTableSelection) {
      return;
    }

    const tableAttrs = editor.getAttributes('table');
    const cellAttrs = editor.getAttributes('tableCell');
    const tableStyle = parseStyle(tableAttrs.style);
    const cellStyle = parseStyle(cellAttrs.style);

    const widthRaw = String(tableStyle.width || '').trim().toLowerCase();
    let widthPreset: TablePropertiesState['widthPreset'] = defaultTableProperties.widthPreset;
    let preferredWidthUnit: TablePropertiesState['preferredWidthUnit'] = defaultTableProperties.preferredWidthUnit;
    let preferredWidth = extractNumericText(tableStyle.width) || defaultTableProperties.preferredWidth;

    if (widthRaw === 'auto') {
      widthPreset = 'AUTO';
      preferredWidth = '';
    } else if (widthRaw.endsWith('%')) {
      preferredWidthUnit = '%';
      const widthValue = extractNumericText(widthRaw) || defaultTableProperties.preferredWidth;
      if (widthValue === '100' || widthValue === '75' || widthValue === '50') {
        widthPreset = widthValue as TablePropertiesState['widthPreset'];
      } else {
        widthPreset = 'CUSTOM';
      }
      preferredWidth = widthValue;
    } else if (widthRaw.endsWith('px')) {
      widthPreset = 'CUSTOM';
      preferredWidthUnit = 'px';
      preferredWidth = extractNumericText(widthRaw) || defaultTableProperties.preferredWidth;
    }

    const marginExpanded = expandCssBoxShorthand(tableStyle.margin);

    const nextValues: Partial<TablePropertiesState> = {
      widthPreset,
      preferredWidthUnit,
      preferredWidth,
      columnWidth: extractNumericText(cellStyle.width) || (Array.isArray(cellAttrs.colwidth) && cellAttrs.colwidth.length ? String(cellAttrs.colwidth[0] ?? '') : ''),
      rowHeight: extractNumericText(cellStyle.height),
      minimumRowHeight: extractNumericText(cellStyle['min-height']),
      borderWidth: extractBorderWidth(cellStyle.border) || defaultTableProperties.borderWidth,
      borderColor: extractBorderColor(cellStyle.border) || defaultTableProperties.borderColor,
      cellBackground: cellStyle['background-color'] && cellStyle['background-color'].startsWith('#')
        ? cellStyle['background-color']
        : defaultTableProperties.cellBackground,
      horizontalAlign: (['left', 'center', 'right', 'justify'].includes(cellStyle['text-align'])
        ? cellStyle['text-align']
        : defaultTableProperties.horizontalAlign) as TablePropertiesState['horizontalAlign'],
      verticalAlign: (cellStyle['vertical-align'] === 'middle' || cellStyle['vertical-align'] === 'bottom'
        ? cellStyle['vertical-align']
        : 'top') as TablePropertiesState['verticalAlign'],
      autoFit: tableStyle['table-layout'] === 'auto' ? 'auto' : 'fixed',
      repeatHeaderRow: editor.isActive('tableHeader'),
      allowRowBreak: tableStyle['break-inside'] !== 'avoid',
      cellPadding: extractNumericText(cellStyle.padding) || defaultTableProperties.cellPadding,
      cellSpacing: extractNumericText(tableStyle['border-spacing']) || defaultTableProperties.cellSpacing,
      tableMarginTop: extractNumericText(tableStyle['margin-top'] || marginExpanded.top) || defaultTableProperties.tableMarginTop,
      tableMarginBottom: extractNumericText(tableStyle['margin-bottom'] || marginExpanded.bottom) || defaultTableProperties.tableMarginBottom,
      tableMarginLeft: extractNumericText(tableStyle['margin-left'] || marginExpanded.left) || defaultTableProperties.tableMarginLeft,
      tableMarginRight: extractNumericText(tableStyle['margin-right'] || marginExpanded.right) || defaultTableProperties.tableMarginRight,
    };

    setTableProperties((current) => ({
      ...current,
      ...nextValues,
    }));
  }, [editor, isTableSelection]);

  useEffect(() => {
    if (!editor) {
      return;
    }

    const syncFromEditor = () => {
      syncTablePropertiesFromSelection();
    };

    editor.on('selectionUpdate', syncFromEditor);
    editor.on('update', syncFromEditor);
    syncFromEditor();

    return () => {
      editor.off('selectionUpdate', syncFromEditor);
      editor.off('update', syncFromEditor);
    };
  }, [editor, syncTablePropertiesFromSelection]);

  const deleteCurrentTable = useCallback(() => {
    if (readOnly || !editor) {
      return;
    }

    if (editor.chain().focus().deleteTable().run()) {
      return;
    }

    const { state, view } = editor;
    const { selection } = state;

    // Fallback: delete nearest table node around current selection.
    for (let depth = selection.$from.depth; depth >= 0; depth -= 1) {
      const node = selection.$from.node(depth);
      if (node.type.name !== 'table') {
        continue;
      }

      const from = selection.$from.before(depth);
      const to = selection.$from.after(depth);
      const transaction = state.tr.delete(from, to).setSelection(TextSelection.create(state.tr.doc, Math.max(1, from - 1)));
      view.dispatch(transaction);
      return;
    }

    editor.chain().focus().selectParentNode().deleteSelection().run();
  }, [editor, readOnly]);

  const clearTextFormatting = useCallback(() => {
    if (readOnly || !editor) {
      return;
    }

    editor.chain().focus().unsetAllMarks().clearNodes().run();
  }, [editor, readOnly]);

  const increaseListIndent = useCallback(() => {
    if (readOnly || !editor) {
      return;
    }

    editor.chain().focus().sinkListItem('listItem').run();
  }, [editor, readOnly]);

  const decreaseListIndent = useCallback(() => {
    if (readOnly || !editor) {
      return;
    }

    editor.chain().focus().liftListItem('listItem').run();
  }, [editor, readOnly]);

  const insertElement = useCallback((element: 'heading' | 'paragraph' | 'rich_text' | 'table' | 'image' | 'signature') => {
    if (readOnly || !editor) {
      return;
    }

    if (element === 'heading') {
      editor.chain().focus().insertContent('<h1>Heading</h1>').run();
      return;
    }

    if (element === 'paragraph') {
      editor.chain().focus().insertContent('<p>Paragraph</p>').run();
      return;
    }

    if (element === 'rich_text') {
      editor.chain().focus().insertContent('<p><strong>Rich Text</strong></p>').run();
      return;
    }

    if (element === 'table') {
      editor.chain().focus().insertTable({ rows: 3, cols: 4, withHeaderRow: true }).run();
      return;
    }

    if (element === 'image') {
      editor.chain().focus().insertContent('<p><img src="" alt="Image" /></p>').run();
      return;
    }

    editor.chain().focus().insertContent('<p><strong>Authorised Signatory</strong></p>').run();
  }, [editor, readOnly]);

  const applyAutoPagination = useCallback((doc: PMDoc) => {
    return autoPaginateDoc(doc, {
      pageSize,
      orientation,
      marginPx,
    });
  }, [marginPx, orientation, pageSize]);

  useEffect(() => {
    setActivePage((current) => Math.min(Math.max(1, current), totalPages));
  }, [totalPages]);

  useEffect(() => {
    if (!editor) {
      return;
    }

    const timer = window.setTimeout(() => {
      const currentDoc = normalizeProseMirrorDoc(editor.getJSON()) as PMDoc;
      const normalized = normalizeDocForEnterpriseVariables(currentDoc);
      const paginated = applyAutoPagination(normalized);
      setEditorContent(editor, paginated, false);
    }, 120);

    return () => {
      window.clearTimeout(timer);
    };
  }, [applyAutoPagination, editor, marginPx, orientation, pageSize]);

  const jumpToPage = useCallback((targetPage: number) => {
    if (!editor) {
      return;
    }
    const safePage = Math.min(Math.max(1, targetPage), totalPages);
    if (safePage <= 1) {
      editor.chain().focus('start').run();
      setActivePage(1);
      return;
    }

    const positions = getPageBreakPositions(editor);
    const pageBreakPos = positions[safePage - 2];
    if (typeof pageBreakPos === 'number') {
      editor.chain().focus(Math.min(pageBreakPos + 1, editor.state.doc.content.size)).run();
      setActivePage(safePage);
    }
  }, [editor, totalPages]);

  const handleWordImport = useCallback(async (file: File) => {
    const parsed = await parseWordMutation.mutateAsync(file);
    if (!editor) {
      return;
    }

    const normalized = normalizeProseMirrorDoc(parsed?.prosemirror_json);
    const normalizedWithVariables = normalizeDocForEnterpriseVariables(normalized as PMDoc);
    const paginatedDoc = applyAutoPagination(normalizedWithVariables);

    setEditorContent(editor, paginatedDoc);
    editor.commands.focus('start');

    const importedPageSize = parsed?.layout?.page_size;
    if (importedPageSize && importedPageSize !== 'CUSTOM' && PAGE_SIZE_OPTIONS.includes(importedPageSize as PageSize)) {
      setPageSize(importedPageSize as PageSize);
    }

    const importedOrientation = parsed?.layout?.page_orientation;
    if (importedOrientation && ORIENTATION_OPTIONS.includes(importedOrientation as Orientation)) {
      setOrientation(importedOrientation as Orientation);
    }

    const marginFromLayout = extractMarginPxFromLayout(parsed?.layout?.margins);
    if (marginFromLayout) {
      setMarginPx(marginFromLayout);
    }

    const header = flattenLayoutText(parsed?.layout?.headers?.[0]?.content as Record<string, unknown>[] | undefined);
    const footer = flattenLayoutText(parsed?.layout?.footers?.[0]?.content as Record<string, unknown>[] | undefined);
    setLayoutHeaderText(header);
    setLayoutFooterText(footer);
    setActivePage(1);
  }, [applyAutoPagination, editor, parseWordMutation]);

  const buildTemplatePayload = useCallback(
    (formValues: FormValues): TemplatePayload => {
      const currentDoc = normalizeProseMirrorDoc(editor?.getJSON()) as PMDoc;
      const prosemirrorJson = normalizeDocForEnterpriseVariables(currentDoc);
      return {
        ...formValues,
        content_type: 'application/json',
        prosemirror_json: prosemirrorJson,
        page_size: pageSize,
        page_orientation: orientation,
      };
    },
    [editor, orientation, pageSize],
  );

  const submitHandler = useCallback(
    async (formValues: FormValues) => {
      await onSubmit(buildTemplatePayload(formValues));
    },
    [buildTemplatePayload, onSubmit],
  );

  const handleSendForReviewClick = useCallback(async () => {
    if (!onSendForReview) {
      return;
    }

    await handleSubmit(async (formValues: FormValues) => {
      await onSendForReview(buildTemplatePayload(formValues));
    })();
  }, [buildTemplatePayload, handleSubmit, onSendForReview]);

  return (
    <EditorSelectionProvider editor={editor}>
      <Stack component="form" spacing={1.25} onSubmit={handleSubmit(submitHandler)}>
      <Card variant="outlined">
        <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
          <Stack spacing={1.25}>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.25}>
              <TextField
                label="Template Name"
                fullWidth
                {...register('name')}
                  disabled={readOnly}
                error={Boolean(errors.name)}
                helperText={errors.name?.message}
              />
              <TextField
                label="Template Code"
                fullWidth
                value={values.code ?? ''}
                disabled={readOnly}
                error={Boolean(errors.code)}
                helperText={errors.code?.message ?? 'Code is generated automatically from Template Name.'}
                slotProps={{
                  input: {
                    readOnly: true,
                  },
                }}
              />
              <input type="hidden" {...register('code')} />
            </Stack>

            <Stack direction="row" spacing={1} alignItems="center" sx={{ flexWrap: 'wrap' }}>
              {templateStatus ? <Chip size="small" color="success" label={templateStatus} /> : null}
              {currentVersion ? <Chip size="small" variant="outlined" label={`v${currentVersion}.0${versionCount ? ` (${versionCount} versions)` : ''}`} /> : null}
            </Stack>

            <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.25}>
              <FormControl fullWidth error={Boolean(errors.document_id)}>
                <InputLabel id="template-document-id">Document</InputLabel>
                <Controller
                  name="document_id"
                  control={control}
                  render={({ field }) => (
                    <Select {...field} labelId="template-document-id" label="Document" disabled={readOnly}>
                      {documents.map((document) => (
                        <MenuItem key={document.id} value={document.id}>
                          {document.name}
                        </MenuItem>
                      ))}
                    </Select>
                  )}
                />
              </FormControl>

              <FormControl fullWidth>
                <InputLabel id="template-type-id">Template Type</InputLabel>
                <Controller
                  name="template_type"
                  control={control}
                  render={({ field }) => (
                    <Select {...field} labelId="template-type-id" label="Template Type" disabled={readOnly}>
                      {TEMPLATE_TYPE_OPTIONS.map((item) => (
                        <MenuItem key={item} value={item}>
                          {item}
                        </MenuItem>
                      ))}
                    </Select>
                  )}
                />
              </FormControl>

              <FormControl fullWidth>
                <InputLabel id="template-status-id">Status</InputLabel>
                <Controller
                  name="status"
                  control={control}
                  render={({ field }) => (
                    <Select
                      {...field}
                      labelId="template-status-id"
                      label="Status"
                      disabled={readOnly || Boolean(currentVersion && currentVersion > 0)}
                    >
                      {TEMPLATE_STATUS_OPTIONS.map((item) => (
                        <MenuItem key={item} value={item}>
                          {item}
                        </MenuItem>
                      ))}
                    </Select>
                  )}
                />
              </FormControl>
            </Stack>

            <TextField label="Description" multiline minRows={1} {...register('description')} disabled={readOnly} />

            <FormControlLabel
              control={
                <Controller
                  name="is_default"
                  control={control}
                  render={({ field }) => <Switch checked={field.value} onChange={(_, checked) => field.onChange(checked)} disabled={readOnly} />}
                />
              }
              label="Set as default template"
            />
          </Stack>
        </CardContent>
      </Card>

      {/* Editor Card */}
      <Box sx={{ minWidth: 0 }}>
          <Card variant="outlined">
            <CardContent sx={{ p: 0 }}>
          <Box
            sx={{
              borderBottom: '1px solid #dbe3ee',
              px: 1.25,
              py: 0.75,
              background: 'linear-gradient(90deg, #f6f9ff 0%, #f8fafc 55%, #f2f7ff 100%)',
            }}
          >
            <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
              <Tooltip title="Undo"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().undo().run()} disabled={readOnly}><UndoOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Redo"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().redo().run()} disabled={readOnly}><RedoOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />

              <Select size="small" value={fontFamily} disabled={readOnly} onChange={(event) => {
                const next = event.target.value as (typeof FONT_OPTIONS)[number];
                setFontFamily(next);
                editor?.chain().focus().setFontFamily(next).run();
              }} sx={{ minWidth: 140 }}>
                {FONT_OPTIONS.map((font) => <MenuItem key={font} value={font}>{font}</MenuItem>)}
              </Select>

              <Select size="small" value={fontSize} disabled={readOnly} onChange={(event) => {
                const next = Number(event.target.value);
                setFontSize(next);
                editor?.chain().focus().setMark('textStyle', { fontSize: `${next}px` }).run();
              }} sx={{ width: 82 }}>
                {FONT_SIZE_OPTIONS.map((size) => <MenuItem key={size} value={size}>{size}</MenuItem>)}
              </Select>

              <Tooltip title="Bold"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().toggleBold().run()} disabled={readOnly}><FormatBoldOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Italic"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().toggleItalic().run()} disabled={readOnly}><FormatItalicOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Underline"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().toggleUnderline().run()} disabled={readOnly}><FormatUnderlinedOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Strikethrough"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().toggleStrike().run()} disabled={readOnly}><FormatStrikethroughOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Text Color"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().setColor('#1d4ed8').run()} disabled={readOnly}><FormatColorTextOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Highlight"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().toggleHighlight({ color: '#fef08a' }).run()} disabled={readOnly}><FormatColorFillOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Clear Formatting"><span><IconButton size="small" sx={ribbonButtonSx} onClick={clearTextFormatting} disabled={readOnly}><FormatClearOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>

              <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />
              <Tooltip title="Align Left"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().setTextAlign('left').run()} disabled={readOnly}><FormatAlignLeftOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Align Center"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().setTextAlign('center').run()} disabled={readOnly}><FormatAlignCenterOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Align Right"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().setTextAlign('right').run()} disabled={readOnly}><FormatAlignRightOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Justify"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().setTextAlign('justify').run()} disabled={readOnly}><FormatAlignJustifyOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Bullet List"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().toggleBulletList().run()} disabled={readOnly}><FormatListBulletedOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Numbered List"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().toggleOrderedList().run()} disabled={readOnly}><FormatListNumberedOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Increase Indent (List)"><span><IconButton size="small" sx={ribbonButtonSx} onClick={increaseListIndent} disabled={readOnly}><FormatIndentIncreaseOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Decrease Indent (List)"><span><IconButton size="small" sx={ribbonButtonSx} onClick={decreaseListIndent} disabled={readOnly}><FormatIndentDecreaseOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>

              <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />
              <Tooltip title="Insert Link"><span><IconButton size="small" sx={ribbonButtonSx} disabled={readOnly} onClick={() => {
                const href = window.prompt('Enter URL');
                if (href) editor?.chain().focus().extendMarkRange('link').setLink({ href }).run();
              }}><InsertLinkOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Insert Horizontal Line"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().setHorizontalRule().run()} disabled={readOnly}><HorizontalRuleOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Insert Image URL"><span><IconButton size="small" sx={ribbonButtonSx} disabled={readOnly} onClick={() => {
                const src = window.prompt('Enter image URL');
                if (src) editor?.chain().focus().setImage({ src }).run();
              }}><AddPhotoAlternateOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Insert Table"><span><IconButton size="small" sx={ribbonButtonSx} onClick={(event) => setInsertTableMenuAnchor(event.currentTarget)} disabled={readOnly}><TableRowsOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Button size="small" variant="outlined" onClick={() => insertEnterpriseTable('ADDRESS_TABLE')} disabled={readOnly}>Address Table</Button>
              <Button size="small" variant="outlined" onClick={() => insertEnterpriseTable('PAYMENT_SCHEDULE')} disabled={readOnly}>Payment Schedule</Button>
              <Button size="small" variant="outlined" onClick={insertSignatureTable} disabled={readOnly}>Signature Table</Button>
              <Tooltip title="Delete Table"><span><IconButton size="small" sx={ribbonButtonSx} onClick={deleteCurrentTable} disabled={readOnly || !isTableSelection}><DeleteOutlineOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Insert Page Break"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().insertContent({ type: 'pageBreak', attrs: { auto: false, source: 'manual' } }).run()} disabled={readOnly}><SplitscreenOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Insert Header"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().insertContent('<p><strong>Header</strong></p>').run()} disabled={readOnly}><VerticalAlignTopOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <Tooltip title="Insert Footer"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => editor?.chain().focus().insertContent('<p><strong>Footer</strong></p>').run()} disabled={readOnly}><VerticalAlignBottomOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>

              <Button size="small" variant="outlined" onClick={() => runTableCommand((current) => current.chain().addRowBefore().run())} disabled={readOnly || !isTableSelection}>Row Before</Button>
              <Button size="small" variant="outlined" onClick={() => runTableCommand((current) => current.chain().addRowAfter().run())} disabled={readOnly || !isTableSelection}>Row After</Button>
              <Button size="small" variant="outlined" onClick={() => runTableCommand((current) => current.chain().deleteRow().run())} disabled={readOnly || !isTableSelection}>Row Delete</Button>
              <Button size="small" variant="outlined" onClick={() => runTableCommand((current) => current.chain().addColumnBefore().run())} disabled={readOnly || !isTableSelection}>Column Before</Button>
              <Button size="small" variant="outlined" onClick={() => runTableCommand((current) => current.chain().addColumnAfter().run())} disabled={readOnly || !isTableSelection}>Column After</Button>
              <Button size="small" variant="outlined" onClick={() => runTableCommand((current) => current.chain().deleteColumn().run())} disabled={readOnly || !isTableSelection}>Column Delete</Button>
              <Button size="small" variant="outlined" onClick={() => runTableCommand((current) => current.chain().mergeCells().run())} disabled={readOnly || !isTableSelection}>Merge Cells</Button>
              <Button size="small" variant="outlined" onClick={() => runTableCommand((current) => current.chain().splitCell().run())} disabled={readOnly || !isTableSelection}>Split Cells</Button>
              <Button size="small" variant="outlined" onClick={() => runTableCommand((current) => current.chain().toggleHeaderRow().run())} disabled={readOnly || !isTableSelection}>Header Row</Button>
              <Button size="small" variant="outlined" onClick={() => runTableCommand((current) => current.chain().toggleHeaderColumn().run())} disabled={readOnly || !isTableSelection}>Header Column</Button>
              <Button size="small" variant="outlined" onClick={() => runTableCommand((current) => current.chain().toggleHeaderCell().run())} disabled={readOnly || !isTableSelection}>Header Cell</Button>
              <Button size="small" variant="outlined" onClick={() => setTablePropertiesOpen(true)} disabled={readOnly || !isTableSelection}>Table Properties</Button>

              <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />
              <Select size="small" value={pageSize} disabled={readOnly} onChange={(event) => setPageSize(event.target.value as PageSize)} sx={{ width: 100 }}>
                {PAGE_SIZE_OPTIONS.map((size) => <MenuItem key={size} value={size}>{size}</MenuItem>)}
              </Select>
              <Select size="small" value={orientation} disabled={readOnly} onChange={(event) => setOrientation(event.target.value as Orientation)} sx={{ width: 120 }}>
                {ORIENTATION_OPTIONS.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}
              </Select>
              <TextField
                size="small"
                label="Margins"
                type="number"
                value={marginPx}
                disabled={readOnly}
                onChange={(event) => setMarginPx(Math.max(16, Number(event.target.value) || 16))}
                sx={{ width: 110 }}
                inputProps={{ min: 16, max: 120 }}
              />

              <Tooltip title="Previous Page"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => jumpToPage(activePage - 1)} disabled={readOnly || activePage <= 1}><NavigateBeforeOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>
              <TextField
                size="small"
                label="Page"
                type="number"
                value={activePage}
                onChange={(event) => jumpToPage(Number(event.target.value || 1))}
                sx={{ width: 90 }}
                inputProps={{ min: 1, max: totalPages }}
              />
              <Typography variant="caption" sx={{ color: '#475569', minWidth: 24, textAlign: 'center' }}>
                / {totalPages}
              </Typography>
              <Tooltip title="Next Page"><span><IconButton size="small" sx={ribbonButtonSx} onClick={() => jumpToPage(activePage + 1)} disabled={readOnly || activePage >= totalPages}><NavigateNextOutlinedIcon fontSize="small" /></IconButton></span></Tooltip>

              <ZoomInOutlinedIcon sx={{ fontSize: 16, color: '#64748b' }} />
              <Select
                size="small"
                value={zoomPercent}
                onChange={(event) => setZoomPercent(Number(event.target.value))}
                sx={{ width: 95 }}
              >
                {[70, 80, 90, 100, 110, 125, 150].map((zoom) => (
                  <MenuItem key={zoom} value={zoom}>{zoom}%</MenuItem>
                ))}
              </Select>

              <Divider orientation="vertical" flexItem sx={{ mx: 0.5 }} />
              <Button
                size="small"
                variant="outlined"
                startIcon={<PrintOutlinedIcon />}
                onClick={() => {
                  const currentDoc = normalizeProseMirrorDoc(editor?.getJSON()) as PMDoc;
                  const paginated = applyAutoPagination(normalizeDocForEnterpriseVariables(currentDoc));
                  if (editor) {
                    setEditorContent(editor, paginated);
                  }
                }}
                disabled={readOnly || !editor}
              >
                Re-paginate
              </Button>
              <Button
                size="small"
                variant="outlined"
                startIcon={<UploadFileOutlinedIcon />}
                onClick={() => fileInputRef.current?.click()}
                disabled={readOnly || parseWordMutation.isPending}
              >
                Import Word
              </Button>
              <input
                ref={fileInputRef}
                type="file"
                accept=".doc,.docx"
                hidden
                onChange={async (event) => {
                  const file = event.target.files?.[0];
                  if (!file) return;
                  await handleWordImport(file);
                  event.target.value = '';
                }}
              />
            </Stack>
          </Box>

          <Stack direction={{ xs: 'column', lg: 'row' }}>
            <Box
              sx={{
                width: { xs: '100%', lg: 260 },
                borderRight: { lg: '1px solid #e4eaf3' },
                borderBottom: { xs: '1px solid #e4eaf3', lg: 'none' },
                p: 0,
                background: 'linear-gradient(180deg, #f8fbff 0%, #f4f7fc 100%)',
              }}
            >
              <Box sx={{ px: 1.25, py: 0.75, backgroundColor: '#0b5cab' }}>
                <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#fff' }}>
                  Design Panel
                </Typography>
              </Box>
              <Tabs
                value={designTab}
                onChange={(_event, value) => setDesignTab(value)}
                variant="fullWidth"
                sx={{
                  minHeight: 36,
                  borderBottom: '1px solid #d9e3f2',
                  '& .MuiTab-root': { minHeight: 36, fontSize: '0.8rem', textTransform: 'none' },
                }}
              >
                <Tab value="elements" label="Elements" />
                <Tab value="fields" label="Fields" />
              </Tabs>

              <Box sx={{ p: 1.25 }}>
                {designTab === 'elements' ? (
                  <>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 800, color: '#1e3a8a' }}>
                      Elements
                    </Typography>
                    <Box
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
                        gap: 1,
                        mb: 1.5,
                      }}
                    >
                      <Paper
                        variant="outlined"
                        onClick={() => insertElement('heading')}
                        sx={{ p: 1, textAlign: 'center', cursor: readOnly ? 'default' : 'pointer', borderColor: '#d7e2f2' }}
                      >
                        <TitleOutlinedIcon fontSize="small" color="primary" />
                        <Typography variant="caption" display="block">Heading</Typography>
                      </Paper>
                      <Paper
                        variant="outlined"
                        onClick={() => insertElement('paragraph')}
                        sx={{ p: 1, textAlign: 'center', cursor: readOnly ? 'default' : 'pointer', borderColor: '#d7e2f2' }}
                      >
                        <SubjectOutlinedIcon fontSize="small" color="primary" />
                        <Typography variant="caption" display="block">Paragraph</Typography>
                      </Paper>
                      <Paper
                        variant="outlined"
                        onClick={() => insertElement('rich_text')}
                        sx={{ p: 1, textAlign: 'center', cursor: readOnly ? 'default' : 'pointer', borderColor: '#d7e2f2' }}
                      >
                        <TextFieldsOutlinedIcon fontSize="small" color="primary" />
                        <Typography variant="caption" display="block">Rich Text</Typography>
                      </Paper>
                      <Paper
                        variant="outlined"
                        onClick={() => insertElement('image')}
                        sx={{ p: 1, textAlign: 'center', cursor: readOnly ? 'default' : 'pointer', borderColor: '#d7e2f2' }}
                      >
                        <AddPhotoAlternateOutlinedIcon fontSize="small" color="primary" />
                        <Typography variant="caption" display="block">Image</Typography>
                      </Paper>
                      <Paper
                        variant="outlined"
                        onClick={() => insertElement('table')}
                        sx={{ p: 1, textAlign: 'center', cursor: readOnly ? 'default' : 'pointer', borderColor: '#d7e2f2' }}
                      >
                        <TableRowsOutlinedIcon fontSize="small" color="primary" />
                        <Typography variant="caption" display="block">Table</Typography>
                      </Paper>
                      <Paper
                        variant="outlined"
                        onClick={() => insertElement('signature')}
                        sx={{ p: 1, textAlign: 'center', cursor: readOnly ? 'default' : 'pointer', borderColor: '#d7e2f2' }}
                      >
                        <UploadFileOutlinedIcon fontSize="small" color="primary" />
                        <Typography variant="caption" display="block">Signature</Typography>
                      </Paper>
                    </Box>

                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 700 }}>Other Components</Typography>
                    <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
                      <Chip label="Dynamic Collections" icon={<ViewAgendaOutlinedIcon />} size="small" onClick={() => editor?.chain().focus().insertContent('<p><strong>Dynamic Collection</strong></p>').run()} />
                    </Stack>
                  </>
                ) : (
                  <>
                    <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 700 }}>Variables</Typography>
                    {variablesQuery.isError ? <Alert severity="warning">Failed to load variables for this document.</Alert> : null}
                    <List dense disablePadding>
                      {groupedVariables.map((group) => (
                        <Box key={group.name} sx={{ mb: 1.5 }}>
                          <Typography variant="caption" sx={{ color: '#475569', fontWeight: 700 }}>{group.name}</Typography>
                          {group.items.map((item) => (
                            <ListItemButton
                              key={item.token}
                              draggable
                              onDragStart={(event) => {
                                event.dataTransfer.setData(
                                  'application/eddp-variable',
                                  JSON.stringify({ token: item.token, label: item.label }),
                                );
                                event.dataTransfer.effectAllowed = 'copy';
                              }}
                              onClick={() => {
                                if (readOnly) return;
                                editor?.chain().focus().insertContent({
                                  type: 'variableChip',
                                  attrs: { field: item.token, label: item.label },
                                }).run();
                              }}
                              sx={{ py: 0.5, px: 1, borderRadius: 1 }}
                            >
                              <ListItemText
                                primaryTypographyProps={{ variant: 'body2' }}
                                primary={item.label}
                                secondary={`<${item.token}>`}
                              />
                            </ListItemButton>
                          ))}
                        </Box>
                      ))}
                    </List>
                  </>
                )}

                <Divider sx={{ my: 1.25 }} />
                <Typography variant="subtitle2" sx={{ mb: 0.75, fontWeight: 700 }}>
                  Pages
                </Typography>
                <Stack spacing={0.75} sx={{ maxHeight: 200, overflowY: 'auto', pr: 0.5 }}>
                  {Array.from({ length: totalPages }).map((_, index) => {
                    const page = index + 1;
                    const active = page === activePage;
                    return (
                      <Paper
                        key={page}
                        variant="outlined"
                        onClick={() => jumpToPage(page)}
                        sx={{
                          p: 0.75,
                          cursor: 'pointer',
                          borderColor: active ? '#2563eb' : '#d7e2f2',
                          backgroundColor: active ? '#eff6ff' : '#ffffff',
                        }}
                      >
                        <Typography variant="caption" sx={{ fontWeight: 700, color: active ? '#1d4ed8' : '#334155' }}>
                          Page {page}
                        </Typography>
                      </Paper>
                    );
                  })}
                </Stack>
              </Box>
            </Box>

            <Box
              sx={{
                flex: 1,
                p: { xs: 0.75, md: 1 },
                background:
                  'radial-gradient(circle at 15% 15%, rgba(191, 219, 254, 0.6), transparent 35%), radial-gradient(circle at 85% 35%, rgba(147, 197, 253, 0.35), transparent 35%), #e9edf5',
                display: 'flex',
                justifyContent: 'flex-start',
                alignItems: 'flex-start',
                flexDirection: 'column',
                gap: 1,
              }}
            >
              <Paper
                variant="outlined"
                sx={{
                  width: pageDimension.width,
                  maxWidth: '100%',
                  px: 1.5,
                  py: 0.75,
                  borderColor: '#d4deec',
                  backgroundColor: '#f8fbff',
                }}
              >
                <Box sx={{ position: 'relative', height: 18 }}>
                  {Array.from({ length: 17 }).map((_, index) => {
                    const major = index % 2 === 0;
                    return (
                      <Box
                        key={index}
                        sx={{
                          position: 'absolute',
                          left: `${(index / 16) * 100}%`,
                          top: 0,
                          width: '1px',
                          height: major ? 14 : 8,
                          bgcolor: major ? '#64748b' : '#94a3b8',
                        }}
                      />
                    );
                  })}
                </Box>
              </Paper>

              <Paper
                variant="outlined"
                sx={{
                  width: pageDimension.width,
                  maxWidth: '100%',
                  minHeight: pageDimension.height,
                  margin: 0,
                  p: `${marginPx}px`,
                  boxSizing: 'border-box',
                  backgroundColor: '#fff',
                  position: 'relative',
                  overflow: 'visible',
                  borderColor: '#d4deec',
                  boxShadow: '0 18px 40px rgba(15, 23, 42, 0.08)',
                  transform: `scale(${zoomPercent / 100})`,
                  transformOrigin: 'top left',
                  '& .enterprise-doc-editor': {
                    minHeight: `calc(${pageDimension.height}px - ${marginPx * 2}px)`,
                    outline: 'none',
                    fontFamily,
                    fontSize: `${fontSize}px`,
                    color: '#111827',
                    lineHeight: 1.6,
                  },
                  '& .enterprise-doc-editor p': { margin: '0 0 12px 0' },
                  '& .enterprise-doc-editor h1': { margin: '0 0 14px 0', fontSize: '2rem' },
                  '& .enterprise-doc-editor h2': { margin: '0 0 12px 0', fontSize: '1.6rem' },
                  '& .enterprise-doc-editor ul, & .enterprise-doc-editor ol': { margin: '0 0 12px 20px' },
                  '& .enterprise-doc-editor table': { width: '100%', borderCollapse: 'collapse', marginBottom: 16 },
                  '& .enterprise-doc-editor table:hover': {
                    outline: '2px solid #93c5fd',
                    outlineOffset: '2px',
                  },
                  '& .enterprise-doc-editor table.eddp-selected-table': {
                    outline: '2px solid #2563eb',
                    outlineOffset: '2px',
                  },
                  '& .enterprise-doc-editor .tableWrapper': {
                    position: 'relative',
                  },
                  '& .enterprise-doc-editor th, & .enterprise-doc-editor td': {
                    border: '1px solid #d1d5db',
                    padding: '6px 8px',
                    verticalAlign: 'top',
                  },
                  '& .enterprise-doc-editor th.selectedCell, & .enterprise-doc-editor td.selectedCell': {
                    backgroundColor: 'rgba(37, 99, 235, 0.15)',
                  },
                  '& .enterprise-doc-editor img': { maxWidth: '100%', height: 'auto' },
                  '& .variable-chip': {
                    display: 'inline',
                    color: 'inherit',
                    padding: 0,
                    fontSize: 'inherit',
                    lineHeight: 'inherit',
                    fontWeight: 'inherit',
                    fontFamily: 'inherit',
                    whiteSpace: 'nowrap',
                    margin: 0,
                    verticalAlign: 'baseline',
                    border: 'none',
                    backgroundColor: 'transparent',
                    borderRadius: 0,
                  },
                  '& .variable-chip-simple': {
                    borderColor: 'transparent',
                    backgroundColor: 'transparent',
                    color: 'inherit',
                  },
                  '& .variable-chip-dynamic-table': {
                    borderColor: 'transparent',
                    backgroundColor: 'transparent',
                    color: 'inherit',
                  },
                  '& .variable-chip-signature': {
                    borderColor: 'transparent',
                    backgroundColor: 'transparent',
                    color: 'inherit',
                  },
                  '& .variable-chip-image': {
                    borderColor: 'transparent',
                    backgroundColor: 'transparent',
                    color: 'inherit',
                  },
                  '& .et-change-inline': {
                    borderRadius: '2px',
                    padding: '0 1px',
                    transition: 'background-color 120ms ease',
                  },
                  '& .et-change-added': {
                    color: '#166534',
                    textDecoration: 'underline',
                    textDecorationThickness: '1.5px',
                    backgroundColor: 'rgba(22, 163, 74, 0.08)',
                  },
                  '& .et-change-removed': {
                    color: '#b91c1c',
                    textDecoration: 'line-through',
                    backgroundColor: 'rgba(220, 38, 38, 0.08)',
                  },
                  '& .et-change-modified': {
                    color: '#92400e',
                    backgroundColor: 'rgba(245, 158, 11, 0.2)',
                  },
                  '& .et-change-format': {
                    backgroundColor: 'rgba(126, 34, 206, 0.12)',
                    boxShadow: 'inset 0 -2px 0 rgba(126, 34, 206, 0.35)',
                  },
                  '& .et-change-position': {
                    backgroundColor: 'rgba(37, 99, 235, 0.12)',
                    boxShadow: 'inset 0 -2px 0 rgba(37, 99, 235, 0.45)',
                  },
                  '& .et-change-image': {
                    backgroundColor: 'rgba(234, 88, 12, 0.12)',
                    boxShadow: 'inset 0 -2px 0 rgba(234, 88, 12, 0.45)',
                  },
                  '& .et-change-table': {
                    backgroundColor: 'rgba(15, 118, 110, 0.12)',
                    boxShadow: 'inset 0 -2px 0 rgba(15, 118, 110, 0.45)',
                  },
                  '& .et-change-variable': {
                    backgroundColor: 'rgba(29, 78, 216, 0.12)',
                    boxShadow: 'inset 0 -2px 0 rgba(29, 78, 216, 0.45)',
                  },
                  '& .et-change-deleted-widget': {
                    color: '#b91c1c',
                    textDecoration: 'line-through',
                    marginRight: '4px',
                    opacity: 0.95,
                  },
                  '& .page-break': {
                    border: 'none',
                    borderTop: '2px dashed #94a3b8',
                    margin: '20px 0',
                  },
                  '& .page-break-auto': {
                    borderTopColor: '#60a5fa',
                    opacity: 0.9,
                  },
                  '& .page-break-manual': {
                    borderTopColor: '#334155',
                  },
                  '@media print': {
                    boxShadow: 'none',
                    border: 'none',
                    transform: 'none',
                    '& .enterprise-doc-editor table': {
                      breakInside: 'auto',
                    },
                    '& .enterprise-doc-editor tr': {
                      breakInside: 'avoid',
                    },
                    '& .enterprise-doc-editor thead': {
                      display: 'table-header-group',
                    },
                    '& .page-break': {
                      breakAfter: 'page',
                      borderTop: 'none',
                      height: 0,
                      margin: 0,
                    },
                  },
                }}
              >
                {layoutHeaderText ? (
                  <Typography variant="caption" sx={{ display: 'block', color: '#64748b', borderBottom: '1px solid #e2e8f0', mb: 1, pb: 0.5 }}>
                    {layoutHeaderText}
                  </Typography>
                ) : null}
                <Box sx={readOnly ? { pointerEvents: 'none' } : undefined}>
                  <EditorContent editor={editor} />
                </Box>
                {layoutFooterText ? (
                  <Typography variant="caption" sx={{ display: 'block', color: '#64748b', borderTop: '1px solid #e2e8f0', mt: 1, pt: 0.5 }}>
                    {layoutFooterText}
                  </Typography>
                ) : null}
                {/* Selection Status Display - Demonstrates EditorSelectionContext Integration */}
                <SelectionStatusBar />
                {reviewChanges.length > 0 ? (
                  <TrackChangesOverlay
                    editor={editor}
                    changes={reviewChanges}
                    versionLabel={versionLabel || (currentVersion ? `v${currentVersion}.0` : 'Current')}
                    documentId={documentId}
                    onReview={onReviewChange}
                    disabled={reviewActionsDisabled}
                  />
                ) : null}
                <Typography
                  variant="caption"
                  sx={{
                    position: 'absolute',
                    right: 12,
                    bottom: 8,
                    color: '#94a3b8',
                  }}
                >
                  Page {activePage} of {totalPages}
                </Typography>
              </Paper>
            </Box>
          </Stack>
        </CardContent>
      </Card>
      </Box>

      <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} justifyContent="flex-end" alignItems={{ xs: 'stretch', md: 'center' }}>
        <Stack direction="row" spacing={1}>
          {!readOnly && onSendForReview ? (
            <Button
              variant="outlined"
              color="primary"
              onClick={() => {
                void handleSendForReviewClick();
              }}
              disabled={isSubmitting}
            >
              Send For Review
            </Button>
          ) : null}
          {!readOnly && onApprove ? (
            <Button variant="outlined" color="success" onClick={onApprove} disabled={isSubmitting}>
              Approve
            </Button>
          ) : null}
          {!readOnly ? <Button type="submit" variant="contained" startIcon={<SaveOutlinedIcon />} disabled={isSubmitting}>
            {isSubmitting ? 'Saving...' : 'Save Template'}
          </Button> : null}
        </Stack>
      </Stack>

      <Popover
        open={Boolean(insertTableMenuAnchor)}
        anchorEl={insertTableMenuAnchor}
        onClose={() => {
          setInsertTableMenuAnchor(null);
          setHoverRows(0);
          setHoverCols(0);
        }}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <Box sx={{ p: 1.5, width: 300 }}>
          <Typography variant="body2" sx={{ mb: 1, color: '#334155', fontWeight: 600 }}>
            Insert Table
          </Typography>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: 'repeat(10, 1fr)',
              gap: 0.5,
              mb: 1,
            }}
          >
            {Array.from({ length: 80 }).map((_, index) => {
              const row = Math.floor(index / 10) + 1;
              const col = (index % 10) + 1;
              const selected = row <= hoverRows && col <= hoverCols;
              return (
                <Box
                  key={`grid-${row}-${col}`}
                  onMouseEnter={() => {
                    setHoverRows(row);
                    setHoverCols(col);
                  }}
                  onClick={() => {
                    if (!editor || readOnly) {
                      return;
                    }
                    editor.chain().focus().insertTable({ rows: row, cols: col, withHeaderRow: true }).run();
                    setInsertTableMenuAnchor(null);
                  }}
                  sx={{
                    height: 16,
                    border: '1px solid #cbd5e1',
                    cursor: 'pointer',
                    bgcolor: selected ? '#bfdbfe' : '#f8fafc',
                  }}
                />
              );
            })}
          </Box>
          <Typography variant="caption" sx={{ display: 'block', mb: 1, color: '#475569' }}>
            {hoverRows > 0 && hoverCols > 0 ? `${hoverRows} x ${hoverCols}` : 'Hover grid to choose size'}
          </Typography>
          <Stack spacing={0.5}>
            <Button size="small" variant="text" sx={{ justifyContent: 'flex-start' }} onClick={() => setInsertTableDialogOpen(true)}>
              Insert Table Dialog
            </Button>
            <Button size="small" variant="text" sx={{ justifyContent: 'flex-start' }} disabled>
              Draw Table (planned)
            </Button>
            <Button size="small" variant="text" sx={{ justifyContent: 'flex-start' }} disabled>
              Convert Text to Table (planned)
            </Button>
            <Button size="small" variant="text" sx={{ justifyContent: 'flex-start' }} disabled>
              Quick Tables / Excel Table (planned)
            </Button>
          </Stack>
        </Box>
      </Popover>

      <Menu
        open={tableContextMenu.open}
        onClose={closeTableContextMenu}
        anchorReference="anchorPosition"
        anchorPosition={
          tableContextMenu.open
            ? { top: tableContextMenu.mouseY, left: tableContextMenu.mouseX }
            : undefined
        }
      >
        <MenuItem onClick={() => { runTableCommand((current) => current.chain().addRowBefore().run()); closeTableContextMenu(); }}>Insert Row Above</MenuItem>
        <MenuItem onClick={() => { runTableCommand((current) => current.chain().addRowAfter().run()); closeTableContextMenu(); }}>Insert Row Below</MenuItem>
        <MenuItem onClick={() => { runTableCommand((current) => current.chain().addColumnBefore().run()); closeTableContextMenu(); }}>Insert Column Left</MenuItem>
        <MenuItem onClick={() => { runTableCommand((current) => current.chain().addColumnAfter().run()); closeTableContextMenu(); }}>Insert Column Right</MenuItem>
        <Divider />
        <MenuItem onClick={() => { runTableCommand((current) => current.chain().deleteRow().run()); closeTableContextMenu(); }}>Delete Row</MenuItem>
        <MenuItem onClick={() => { runTableCommand((current) => current.chain().deleteColumn().run()); closeTableContextMenu(); }}>Delete Column</MenuItem>
        <MenuItem onClick={() => { deleteCurrentTable(); closeTableContextMenu(); }}>Delete Table</MenuItem>
        <Divider />
        <MenuItem onClick={() => { runTableCommand((current) => current.chain().mergeCells().run()); closeTableContextMenu(); }}>Merge Cells</MenuItem>
        <MenuItem onClick={() => { runTableCommand((current) => current.chain().splitCell().run()); closeTableContextMenu(); }}>Split Cell</MenuItem>
        <Divider />
        <MenuItem onClick={() => { setTablePropertiesOpen(true); closeTableContextMenu(); }}>Table Properties</MenuItem>
      </Menu>

      <Dialog open={insertTableDialogOpen} onClose={() => setInsertTableDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Insert Table</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 0.5 }}>
            <TextField
              label="Rows"
              type="number"
              value={insertTableRows}
              onChange={(event) => setInsertTableRows(Math.max(1, Number(event.target.value) || 1))}
              inputProps={{ min: 1, max: 100 }}
            />
            <TextField
              label="Columns"
              type="number"
              value={insertTableCols}
              onChange={(event) => setInsertTableCols(Math.max(1, Number(event.target.value) || 1))}
              inputProps={{ min: 1, max: 20 }}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setInsertTableDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={() => {
              if (!editor || readOnly) {
                return;
              }
              editor.chain().focus().insertTable({ rows: insertTableRows, cols: insertTableCols, withHeaderRow: true }).run();
              setInsertTableDialogOpen(false);
              setInsertTableMenuAnchor(null);
            }}
          >
            Insert
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog
        open={tablePropertiesOpen}
        onClose={() => setTablePropertiesOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Table Properties</DialogTitle>
        <DialogContent>
          {!isTableSelection ? (
            <Typography variant="body2" sx={{ mt: 1, color: '#475569' }}>
              Select a table to edit properties.
            </Typography>
          ) : (
            <Stack spacing={2} sx={{ mt: 0.5 }}>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
                <FormControl size="small" fullWidth>
                  <InputLabel>Width Preset</InputLabel>
                  <Select
                    label="Width Preset"
                    value={tableProperties.widthPreset}
                    onChange={(event) => setTableProperties((current) => ({
                      ...current,
                      widthPreset: event.target.value as TablePropertiesState['widthPreset'],
                    }))}
                  >
                    <MenuItem value="AUTO">Auto</MenuItem>
                    <MenuItem value="100">Full (100%)</MenuItem>
                    <MenuItem value="75">Wide (75%)</MenuItem>
                    <MenuItem value="50">Half (50%)</MenuItem>
                    <MenuItem value="CUSTOM">Custom</MenuItem>
                  </Select>
                </FormControl>
                <FormControl size="small" fullWidth disabled={tableProperties.widthPreset !== 'CUSTOM'}>
                  <InputLabel>Width Unit</InputLabel>
                  <Select
                    label="Width Unit"
                    value={tableProperties.preferredWidthUnit}
                    onChange={(event) => setTableProperties((current) => ({
                      ...current,
                      preferredWidthUnit: event.target.value as TablePropertiesState['preferredWidthUnit'],
                    }))}
                  >
                    <MenuItem value="%">Percentage (%)</MenuItem>
                    <MenuItem value="px">Fixed Pixels (px)</MenuItem>
                  </Select>
                </FormControl>
              </Stack>

              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
                <TextField
                  fullWidth
                  size="small"
                  label={tableProperties.preferredWidthUnit === '%' ? 'Custom Width (%)' : 'Custom Width (px)'}
                  type="number"
                  value={tableProperties.preferredWidth}
                  onChange={(event) => setTableProperties((current) => ({ ...current, preferredWidth: event.target.value }))}
                  inputProps={tableProperties.preferredWidthUnit === '%' ? { min: 10, max: 100 } : { min: 60, max: 2000 }}
                  disabled={tableProperties.widthPreset !== 'CUSTOM'}
                />
                <TextField
                  fullWidth
                  size="small"
                  label="Column Width (px)"
                  type="number"
                  value={tableProperties.columnWidth}
                  onChange={(event) => setTableProperties((current) => ({ ...current, columnWidth: event.target.value }))}
                />
              </Stack>

              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
                <TextField
                  fullWidth
                  size="small"
                  label="Cell Padding (px)"
                  type="number"
                  value={tableProperties.cellPadding}
                  onChange={(event) => setTableProperties((current) => ({ ...current, cellPadding: event.target.value }))}
                  inputProps={{ min: 0, max: 64 }}
                />
                <TextField
                  fullWidth
                  size="small"
                  label="Cell Spacing (px)"
                  type="number"
                  value={tableProperties.cellSpacing}
                  onChange={(event) => setTableProperties((current) => ({ ...current, cellSpacing: event.target.value }))}
                  inputProps={{ min: 0, max: 64 }}
                />
              </Stack>

              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
                <TextField
                  fullWidth
                  size="small"
                  label="Margin Top (px)"
                  type="number"
                  value={tableProperties.tableMarginTop}
                  onChange={(event) => setTableProperties((current) => ({ ...current, tableMarginTop: event.target.value }))}
                  inputProps={{ min: 0, max: 240 }}
                />
                <TextField
                  fullWidth
                  size="small"
                  label="Margin Bottom (px)"
                  type="number"
                  value={tableProperties.tableMarginBottom}
                  onChange={(event) => setTableProperties((current) => ({ ...current, tableMarginBottom: event.target.value }))}
                  inputProps={{ min: 0, max: 240 }}
                />
              </Stack>

              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
                <TextField
                  fullWidth
                  size="small"
                  label="Margin Left (px)"
                  type="number"
                  value={tableProperties.tableMarginLeft}
                  onChange={(event) => setTableProperties((current) => ({ ...current, tableMarginLeft: event.target.value }))}
                  inputProps={{ min: 0, max: 240 }}
                />
                <TextField
                  fullWidth
                  size="small"
                  label="Margin Right (px)"
                  type="number"
                  value={tableProperties.tableMarginRight}
                  onChange={(event) => setTableProperties((current) => ({ ...current, tableMarginRight: event.target.value }))}
                  inputProps={{ min: 0, max: 240 }}
                />
              </Stack>

              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
                <TextField
                  fullWidth
                  size="small"
                  label="Row Height (px)"
                  type="number"
                  value={tableProperties.rowHeight}
                  onChange={(event) => setTableProperties((current) => ({ ...current, rowHeight: event.target.value }))}
                />
                <TextField
                  fullWidth
                  size="small"
                  label="Minimum Height (px)"
                  type="number"
                  value={tableProperties.minimumRowHeight}
                  onChange={(event) => setTableProperties((current) => ({ ...current, minimumRowHeight: event.target.value }))}
                />
              </Stack>

              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
                <TextField
                  fullWidth
                  size="small"
                  label="Border Width (px)"
                  type="number"
                  value={tableProperties.borderWidth}
                  onChange={(event) => setTableProperties((current) => ({ ...current, borderWidth: event.target.value }))}
                />
                <TextField
                  fullWidth
                  size="small"
                  label="Border Color"
                  type="color"
                  value={tableProperties.borderColor}
                  onChange={(event) => setTableProperties((current) => ({ ...current, borderColor: event.target.value }))}
                />
                <TextField
                  fullWidth
                  size="small"
                  label="Cell Background"
                  type="color"
                  value={tableProperties.cellBackground}
                  onChange={(event) => setTableProperties((current) => ({ ...current, cellBackground: event.target.value }))}
                />
              </Stack>

              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
                <FormControl size="small" fullWidth>
                  <InputLabel>Horizontal Alignment</InputLabel>
                  <Select
                    label="Horizontal Alignment"
                    value={tableProperties.horizontalAlign}
                    onChange={(event) => setTableProperties((current) => ({
                      ...current,
                      horizontalAlign: event.target.value as TablePropertiesState['horizontalAlign'],
                    }))}
                  >
                    <MenuItem value="left">Left</MenuItem>
                    <MenuItem value="center">Center</MenuItem>
                    <MenuItem value="right">Right</MenuItem>
                    <MenuItem value="justify">Justify</MenuItem>
                  </Select>
                </FormControl>
                <FormControl size="small" fullWidth>
                  <InputLabel>Vertical Alignment</InputLabel>
                  <Select
                    label="Vertical Alignment"
                    value={tableProperties.verticalAlign}
                    onChange={(event) => setTableProperties((current) => ({
                      ...current,
                      verticalAlign: event.target.value as TablePropertiesState['verticalAlign'],
                    }))}
                  >
                    <MenuItem value="top">Top</MenuItem>
                    <MenuItem value="middle">Middle</MenuItem>
                    <MenuItem value="bottom">Bottom</MenuItem>
                  </Select>
                </FormControl>
              </Stack>

              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
                <FormControl size="small" fullWidth>
                  <InputLabel>AutoFit</InputLabel>
                  <Select
                    label="AutoFit"
                    value={tableProperties.autoFit}
                    onChange={(event) => setTableProperties((current) => ({
                      ...current,
                      autoFit: event.target.value as TablePropertiesState['autoFit'],
                    }))}
                  >
                    <MenuItem value="fixed">Fixed Width</MenuItem>
                    <MenuItem value="auto">Auto Fit</MenuItem>
                  </Select>
                </FormControl>
                <FormControlLabel
                  control={(
                    <Switch
                      checked={tableProperties.repeatHeaderRow}
                      onChange={(_, checked) => setTableProperties((current) => ({ ...current, repeatHeaderRow: checked }))}
                    />
                  )}
                  label="Repeat Header Row"
                />
                <FormControlLabel
                  control={(
                    <Switch
                      checked={tableProperties.allowRowBreak}
                      onChange={(_, checked) => setTableProperties((current) => ({ ...current, allowRowBreak: checked }))}
                    />
                  )}
                  label="Allow Row Break"
                />
              </Stack>
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTablePropertiesOpen(false)}>Close</Button>
          <Button
            variant="contained"
            onClick={() => {
              applyTableProperties();
              setTablePropertiesOpen(false);
            }}
            disabled={!isTableSelection}
          >
            Apply
          </Button>
        </DialogActions>
      </Dialog>

      <VariableAutocomplete
        variables={variablesQuery.data ?? []}
        anchorEl={autocompleteAnchorEl}
        searchText={autocompleteSearchText}
        onSelect={handleAutocompleteSelect}
        onClose={closeVariableAutocomplete}
      />
    </Stack>
    </EditorSelectionProvider>
  );
}
