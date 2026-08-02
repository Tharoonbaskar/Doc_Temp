import {
  Box,
  Button,
  Chip,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import FirstPageIcon from '@mui/icons-material/FirstPage';
import LastPageIcon from '@mui/icons-material/LastPage';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined';
import UndoIcon from '@mui/icons-material/Undo';
import ReplyOutlinedIcon from '@mui/icons-material/ReplyOutlined';
import DoneAllOutlinedIcon from '@mui/icons-material/DoneAllOutlined';
import type { Editor } from '@tiptap/react';
import { useEffect, useMemo, useState } from 'react';

import type { ApprovalStatus, ElementChange, ReviewAction, SemanticChangeType } from '../types';

type AnchorInfo = {
  change: ElementChange;
  index: number;
  top: number;
  left: number;
  width: number;
  height: number;
};

type ChangeTone = {
  accent: string;
  softBackground: string;
  border: string;
  markerFill: string;
  markerBorder: string;
};

interface TrackChangesOverlayProps {
  editor: Editor | null;
  changes: ElementChange[];
  versionLabel: string;
  documentId: string;
  onReview?: (changeId: string, action: ReviewAction, comment?: string) => void;
  disabled?: boolean;
}

const toObject = (value: unknown): Record<string, unknown> => {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {};
  return value as Record<string, unknown>;
};

const getTextValue = (value: unknown): string => {
  if (typeof value === 'string') {
    return value.replace(/\r\n/g, '\n');
  }
  const obj = toObject(value);

  const oldText = obj.oldText;
  if (typeof oldText === 'string') return oldText.replace(/\r\n/g, '\n');

  const newText = obj.newText;
  if (typeof newText === 'string') return newText.replace(/\r\n/g, '\n');

  const text = obj.text;
  if (typeof text === 'string') return text.replace(/\r\n/g, '\n');

  const label = obj.label;
  if (typeof label === 'string') return label.replace(/\r\n/g, '\n');

  const binding = obj.binding;
  if (typeof binding === 'string' && binding.trim()) return `{{${binding.trim()}}}`;

  const readFromPm = (node: unknown): string => {
    if (!node || typeof node !== 'object') return '';
    const record = node as Record<string, unknown>;
    const parts: string[] = [];

    const nodeText = record.text;
    if (typeof nodeText === 'string') {
      parts.push(nodeText);
    }

    const attrs = record.attrs;
    if (attrs && typeof attrs === 'object') {
      const attrsRecord = attrs as Record<string, unknown>;
      const bindingValue = attrsRecord.binding;
      const fieldValue = attrsRecord.field;
      if (typeof bindingValue === 'string' && bindingValue.trim()) {
        parts.push(`{{${bindingValue.trim()}}}`);
      } else if (typeof fieldValue === 'string' && fieldValue.trim()) {
        parts.push(`<${fieldValue.trim()}>`);
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

const statusLabel = (status: ApprovalStatus): string => {
  switch (status) {
    case 'APPROVED':
      return 'Approved';
    case 'REJECTED':
      return 'Rejected';
    case 'REVERTED':
      return 'Reverted';
    case 'SENT_BACK':
      return 'Sent Back';
    case 'RESOLVED':
      return 'Resolved';
    default:
      return 'Pending Review';
  }
};

const tokenize = (value: string): string[] =>
  value
    .toLowerCase()
    .split(/\s+/)
    .map((token) => token.trim())
    .filter(Boolean);

const inferTextSemanticType = (
  existingType: SemanticChangeType | undefined,
  oldText: string,
  newText: string,
): SemanticChangeType => {
  const previous = oldText;
  const current = newText;

  if (!previous && current) return 'TEXT_ADDED';
  if (previous && !current) return 'TEXT_REMOVED';

  const previousWithoutWhitespace = previous.replace(/\s+/g, '');
  const currentWithoutWhitespace = current.replace(/\s+/g, '');
  if (previousWithoutWhitespace === currentWithoutWhitespace && previous !== current) {
    return current.length > previous.length ? 'TEXT_ADDED' : 'TEXT_REMOVED';
  }

  if (previous === current) {
    return existingType && existingType !== 'UNKNOWN_CHANGE' ? existingType : 'TEXT_MODIFIED';
  }

  const oldTokens = tokenize(previous);
  const newTokens = tokenize(current);

  const oldCounts = new Map<string, number>();
  oldTokens.forEach((token) => oldCounts.set(token, (oldCounts.get(token) || 0) + 1));

  const newCounts = new Map<string, number>();
  newTokens.forEach((token) => newCounts.set(token, (newCounts.get(token) || 0) + 1));

  let overlap = 0;
  oldCounts.forEach((count, token) => {
    overlap += Math.min(count, newCounts.get(token) || 0);
  });

  const removed = Math.max(oldTokens.length - overlap, 0);
  const added = Math.max(newTokens.length - overlap, 0);
  const similarity = overlap / Math.max(oldTokens.length, newTokens.length, 1);

  if (removed === 0 && added > 0) return 'TEXT_ADDED';
  if (added === 0 && removed > 0) return 'TEXT_REMOVED';

  if (added > 0 && removed > 0 && similarity < 0.35) {
    return 'TEXT_ADDED';
  }

  if (existingType && existingType !== 'UNKNOWN_CHANGE') {
    return existingType;
  }

  return 'TEXT_MODIFIED';
};

const toneForSemanticType = (value: SemanticChangeType): ChangeTone => {
  if (value.endsWith('_ADDED')) {
    return {
      accent: '#166534',
      softBackground: '#ecfdf3',
      border: '#86efac',
      markerFill: '#dcfce7',
      markerBorder: '#16a34a',
    };
  }

  if (value.endsWith('_REMOVED')) {
    return {
      accent: '#b91c1c',
      softBackground: '#fef2f2',
      border: '#fecaca',
      markerFill: '#fee2e2',
      markerBorder: '#dc2626',
    };
  }

  return {
    accent: '#92400e',
    softBackground: '#fffbeb',
    border: '#fcd34d',
    markerFill: '#fef3c7',
    markerBorder: '#f59e0b',
  };
};

const semanticType = (change: ElementChange): SemanticChangeType => {
  const oldText = change.old_text ?? getTextValue(change.old_value);
  const newText = change.new_text ?? getTextValue(change.new_value);

  if (change.semantic_type && change.semantic_type !== 'UNKNOWN_CHANGE' && !change.semantic_type.startsWith('TEXT_')) {
    return change.semantic_type;
  }

  if (change.semantic_type?.startsWith('TEXT_')) {
    return inferTextSemanticType(change.semantic_type, oldText, newText);
  }

  if (change.change_type === 'MODIFIED') {
    return inferTextSemanticType(undefined, oldText, newText);
  }

  if (change.change_type === 'ADDED') return 'TEXT_ADDED';
  if (change.change_type === 'DELETED') return 'TEXT_REMOVED';
  return 'TEXT_MODIFIED';
};

const semanticLabel = (change: ElementChange, resolvedType: SemanticChangeType): string => {
  const hasTableCellCoordinates = Number.isFinite(change.row_index) && Number.isFinite(change.column_index);
  if (hasTableCellCoordinates && resolvedType === 'TABLE_CONTENT_CHANGED') {
    return 'TABLE_CELL_MODIFIED';
  }
  return resolvedType;
};

export function TrackChangesOverlay({
  editor,
  changes,
  versionLabel,
  documentId,
  onReview,
  disabled = false,
}: TrackChangesOverlayProps) {
  const canReview = typeof onReview === 'function';
  const [selectedChangeId, setSelectedChangeId] = useState<string>('');
  const [approvalNotes, setApprovalNotes] = useState<Record<string, string>>({});
  const [reviewerFilter, setReviewerFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<ApprovalStatus | 'ALL'>(() => (canReview ? 'PENDING' : 'ALL'));
  const [typeFilter, setTypeFilter] = useState<SemanticChangeType | 'ALL'>('ALL');
  const [pageFilter, setPageFilter] = useState<number | 'ALL'>('ALL');
  const [navIndex, setNavIndex] = useState(0);
  const [anchorById, setAnchorById] = useState<Record<string, AnchorInfo>>({});

  useEffect(() => {
    setStatusFilter(canReview ? 'PENDING' : 'ALL');
  }, [canReview]);

  const reviewers = useMemo(
    () => Array.from(new Set(changes.map((change) => change.reviewed_by_name).filter(Boolean) as string[])),
    [changes],
  );

  const pages = useMemo(
    () => Array.from(new Set(changes.map((change) => Number(change.page || 1)))).sort((a, b) => a - b),
    [changes],
  );

  const availableTypes = useMemo(
    () => Array.from(new Set(changes.map((change) => semanticType(change)))),
    [changes],
  );

  const filteredChanges = useMemo(() => {
    return changes.filter((change) => {
      const resolvedType = semanticType(change);
      if (reviewerFilter !== 'ALL' && (change.reviewed_by_name || 'UNASSIGNED') !== reviewerFilter) return false;
      if (statusFilter !== 'ALL' && change.approval_status !== statusFilter) return false;
      if (typeFilter !== 'ALL' && resolvedType !== typeFilter) return false;
      if (pageFilter !== 'ALL' && Number(change.page || 1) !== pageFilter) return false;
      return true;
    });
  }, [changes, pageFilter, reviewerFilter, statusFilter, typeFilter]);

  useEffect(() => {
    if (!filteredChanges.length) {
      setSelectedChangeId('');
      setNavIndex(0);
      return;
    }

    const safeIndex = Math.min(navIndex, filteredChanges.length - 1);
    setNavIndex(safeIndex);

    const selected = filteredChanges[safeIndex];
    if (selected) {
      setSelectedChangeId(selected.id);
    }
  }, [filteredChanges, navIndex]);

  useEffect(() => {
    if (!editor) return;

    const recompute = () => {
      const root = editor.view.dom as HTMLElement;
      const rootRect = root.getBoundingClientRect();
      const next: Record<string, AnchorInfo> = {};

      filteredChanges.forEach((change, index) => {
        const node = root.querySelector(`[data-change-id="${change.id}"]`) as HTMLElement | null;
        if (!node) return;

        const rect = node.getBoundingClientRect();
        next[change.id] = {
          change,
          index,
          top: Math.max(rect.top - rootRect.top, 0),
          left: Math.max(rect.left - rootRect.left, 0),
          width: Math.max(rect.width, 80),
          height: Math.max(rect.height, 22),
        };
      });

      setAnchorById(next);
    };

    recompute();
    window.addEventListener('resize', recompute);
    window.addEventListener('scroll', recompute, true);

    return () => {
      window.removeEventListener('resize', recompute);
      window.removeEventListener('scroll', recompute, true);
    };
  }, [editor, filteredChanges]);

  const visibleAnchors = useMemo(() => {
    const anchors = filteredChanges
      .map((change) => anchorById[change.id])
      .filter((item): item is AnchorInfo => Boolean(item));

    if (!editor) return anchors;

    const root = editor.view.dom as HTMLElement;
    const top = root.scrollTop - 260;
    const bottom = root.scrollTop + root.clientHeight + 260;

    return anchors.filter((anchor) => {
      if (anchor.change.id === selectedChangeId) return true;
      return anchor.top >= top && anchor.top <= bottom;
    });
  }, [anchorById, editor, filteredChanges, selectedChangeId]);

  const selectedAnchor = useMemo(
    () => visibleAnchors.find((anchor) => anchor.change.id === selectedChangeId) ?? null,
    [selectedChangeId, visibleAnchors],
  );

  const selectedChange = useMemo(() => {
    if (!filteredChanges.length) return null;
    const fromId = filteredChanges.find((change) => change.id === selectedChangeId);
    if (fromId) return fromId;
    return filteredChanges[Math.max(0, Math.min(navIndex, filteredChanges.length - 1))] ?? null;
  }, [filteredChanges, navIndex, selectedChangeId]);

  const goTo = (targetIndex: number) => {
    if (!filteredChanges.length || !editor) return;
    const bounded = Math.max(0, Math.min(targetIndex, filteredChanges.length - 1));
    const selected = filteredChanges[bounded];
    if (!selected) return;

    setNavIndex(bounded);
    setSelectedChangeId(selected.id);

    const anchor = anchorById[selected.id];
    if (anchor) {
      const root = editor.view.dom as HTMLElement;
      root.scrollTo({ top: Math.max(anchor.top - 100, 0), behavior: 'smooth' });
    }
  };

  return (
    <>
      <Paper
        variant="outlined"
        sx={{
          mt: 1,
          p: 1,
          borderColor: '#d1d5db',
          backgroundColor: '#f8fafc',
          pointerEvents: 'auto',
        }}
      >
        <Stack direction={{ xs: 'column', lg: 'row' }} spacing={1} alignItems={{ lg: 'center' }}>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <IconButton size="small" onClick={() => goTo(0)} disabled={!filteredChanges.length}>
              <FirstPageIcon fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={() => goTo(navIndex - 1)} disabled={!filteredChanges.length}>
              <NavigateBeforeIcon fontSize="small" />
            </IconButton>
            <Typography variant="body2" sx={{ minWidth: 80, textAlign: 'center' }}>
              {filteredChanges.length ? `${navIndex + 1}/${filteredChanges.length}` : '0/0'}
            </Typography>
            <IconButton size="small" onClick={() => goTo(navIndex + 1)} disabled={!filteredChanges.length}>
              <NavigateNextIcon fontSize="small" />
            </IconButton>
            <IconButton size="small" onClick={() => goTo(filteredChanges.length - 1)} disabled={!filteredChanges.length}>
              <LastPageIcon fontSize="small" />
            </IconButton>
          </Stack>

          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel id="reviewer-filter">Reviewer</InputLabel>
            <Select
              labelId="reviewer-filter"
              label="Reviewer"
              value={reviewerFilter}
              onChange={(event) => setReviewerFilter(event.target.value)}
            >
              <MenuItem value="ALL">All Reviewers</MenuItem>
              <MenuItem value="UNASSIGNED">Unassigned</MenuItem>
              {reviewers.map((reviewer) => (
                <MenuItem key={reviewer} value={reviewer}>{reviewer}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 145 }}>
            <InputLabel id="status-filter">Status</InputLabel>
            <Select
              labelId="status-filter"
              label="Status"
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as ApprovalStatus | 'ALL')}
            >
              <MenuItem value="ALL">All Statuses</MenuItem>
              <MenuItem value="PENDING">Pending</MenuItem>
              <MenuItem value="APPROVED">Approved</MenuItem>
              <MenuItem value="REJECTED">Rejected</MenuItem>
              <MenuItem value="REVERTED">Reverted</MenuItem>
              <MenuItem value="SENT_BACK">Sent Back</MenuItem>
              <MenuItem value="RESOLVED">Resolved</MenuItem>
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 210 }}>
            <InputLabel id="type-filter">Change Type</InputLabel>
            <Select
              labelId="type-filter"
              label="Change Type"
              value={typeFilter}
              onChange={(event) => setTypeFilter(event.target.value as SemanticChangeType | 'ALL')}
            >
              <MenuItem value="ALL">All Change Types</MenuItem>
              {availableTypes.map((item) => (
                <MenuItem key={item} value={item}>{item}</MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel id="page-filter">Page</InputLabel>
            <Select
              labelId="page-filter"
              label="Page"
              value={pageFilter}
              onChange={(event) => {
                const value = event.target.value;
                setPageFilter(value === 'ALL' ? 'ALL' : Number(value));
              }}
            >
              <MenuItem value="ALL">All Pages</MenuItem>
              {pages.map((page) => (
                <MenuItem key={page} value={page}>{page}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Stack>
      </Paper>

      <Box sx={{ position: 'absolute', inset: 0, pointerEvents: 'none' }}>
        {visibleAnchors.map((anchor) => {
          const selected = anchor.change.id === selectedChangeId;
          const resolvedType = semanticType(anchor.change);
          const tone = toneForSemanticType(resolvedType);

          return (
            <Box
              key={anchor.change.id}
              sx={{
                position: 'absolute',
                left: anchor.left + anchor.width + 8,
                top: anchor.top,
                width: 14,
                height: 14,
                pointerEvents: 'auto',
                zIndex: selected ? 5 : 3,
              }}
            >
              <Box
                onClick={() => {
                  setSelectedChangeId(anchor.change.id);
                  setNavIndex(anchor.index);
                }}
                sx={{
                  width: 14,
                  height: 14,
                  borderRadius: '50%',
                  border: selected ? `2px solid ${tone.accent}` : `2px solid ${tone.markerBorder}`,
                  backgroundColor: selected ? tone.softBackground : tone.markerFill,
                  cursor: 'pointer',
                }}
              />
            </Box>
          );
        })}

        {selectedChange ? (
          <Box
            sx={{
              position: 'absolute',
              left: 'calc(100% + 24px)',
              top: selectedAnchor?.top ?? 16,
              width: 340,
              maxWidth: 340,
              pointerEvents: 'auto',
              zIndex: 6,
            }}
          >
            {(() => {
              const oldText = selectedChange.old_text ?? getTextValue(selectedChange.old_value);
              const newText = selectedChange.new_text ?? getTextValue(selectedChange.new_value);
              const oldContextText = selectedChange.old_context_text ?? oldText;
              const newContextText = selectedChange.new_context_text ?? newText;
              const resolvedType = semanticType(selectedChange);
              const resolvedLabel = semanticLabel(selectedChange, resolvedType);
              const tone = toneForSemanticType(resolvedType);
              const oldTextDisplay = oldText === '' ? '(empty)' : oldText;
              const newTextDisplay = newText === '' ? '(empty)' : newText;
              const oldTextTooltip = oldText === '' ? '(empty)' : JSON.stringify(oldText);
              const newTextTooltip = newText === '' ? '(empty)' : JSON.stringify(newText);
              const hasTableCellCoordinates = Number.isFinite(selectedChange.row_index) && Number.isFinite(selectedChange.column_index);
              const rowDisplay = hasTableCellCoordinates ? Number(selectedChange.row_index) + 1 : null;
              const columnDisplay = hasTableCellCoordinates ? Number(selectedChange.column_index) + 1 : null;
              const tableDisplay = Number.isFinite(selectedChange.table_index) ? Number(selectedChange.table_index) + 1 : null;

              return (
                <Paper elevation={3} sx={{ p: 1, borderLeft: `4px solid ${tone.accent}`, backgroundColor: '#ffffff', position: 'relative' }}>
                  {selectedAnchor ? (
                    <Box
                      sx={{
                        position: 'absolute',
                        left: -18,
                        top: 20,
                        width: 18,
                        borderTop: `2px solid ${tone.border}`,
                      }}
                    />
                  ) : null}
                  <Stack spacing={0.75}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Tooltip
                        arrow
                        title={
                          <Stack spacing={0.5}>
                            <Typography variant="caption">Change Type: {resolvedLabel}</Typography>
                            <Typography variant="caption">Changed From: {oldTextTooltip}</Typography>
                            <Typography variant="caption">Changed To: {newTextTooltip}</Typography>
                            <Typography variant="caption">Version: {versionLabel}</Typography>
                            <Typography variant="caption">Reviewer: {selectedChange.reviewed_by_name || 'Unassigned'}</Typography>
                            <Typography variant="caption">Reviewed At: {selectedChange.reviewed_at || selectedChange.updated_at || 'N/A'}</Typography>
                            <Typography variant="caption">Status: {statusLabel(selectedChange.approval_status)}</Typography>
                          </Stack>
                        }
                      >
                        <Typography variant="subtitle2" sx={{ fontWeight: 700, cursor: 'help', color: tone.accent }}>
                          {resolvedLabel}
                        </Typography>
                      </Tooltip>
                      <Chip size="small" label={statusLabel(selectedChange.approval_status)} />
                    </Stack>

                    <Typography variant="caption" color="text.secondary">
                      Document: {documentId} | Version: {versionLabel} | Page: {selectedChange.page || 1}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Reviewer: {selectedChange.reviewed_by_name || 'Unassigned'}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      Reviewed At: {selectedChange.reviewed_at ? new Date(selectedChange.reviewed_at).toLocaleString() : 'N/A'}
                    </Typography>

                    {hasTableCellCoordinates ? (
                      <Box sx={{ p: 0.75, borderRadius: 0.75, bgcolor: '#f8fafc', border: '1px solid #cbd5e1' }}>
                        <Typography variant="caption" sx={{ fontWeight: 700 }}>
                          Table Cell Context
                        </Typography>
                        <Typography variant="caption" display="block" color="text.secondary">
                          {tableDisplay !== null ? `Table ${tableDisplay} | ` : ''}Row {rowDisplay} | Column {columnDisplay}
                        </Typography>
                        <Typography variant="caption" display="block" sx={{ whiteSpace: 'pre-wrap' }}>
                          Previous: {oldContextText || '(empty)'}
                        </Typography>
                        <Typography variant="caption" display="block" sx={{ whiteSpace: 'pre-wrap' }}>
                          Current: {newContextText || '(empty)'}
                        </Typography>
                      </Box>
                    ) : null}

                    <Box sx={{ p: 0.75, borderRadius: 0.75, bgcolor: '#fef2f2', border: '1px solid #fecaca' }}>
                      <Typography variant="caption" sx={{ fontWeight: 700 }}>Changed From</Typography>
                      <Typography
                        variant="body2"
                        sx={{
                          color: '#b91c1c',
                          textDecoration: oldText ? 'line-through' : 'none',
                          whiteSpace: 'pre-wrap',
                          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
                        }}
                      >
                        {oldTextDisplay}
                      </Typography>
                    </Box>
                    <Box sx={{ p: 0.75, borderRadius: 0.75, bgcolor: tone.softBackground, border: `1px solid ${tone.border}` }}>
                      <Typography variant="caption" sx={{ fontWeight: 700 }}>Changed To</Typography>
                      <Typography
                        variant="body2"
                        sx={{
                          color: tone.accent,
                          textDecoration: newText ? 'underline' : 'none',
                          whiteSpace: 'pre-wrap',
                          fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
                        }}
                      >
                        {newTextDisplay}
                      </Typography>
                    </Box>

                    {canReview ? (
                      <>
                        <TextField
                          size="small"
                          label="Comments / Approval Notes"
                          placeholder="Add note, reply, approval comment"
                          value={approvalNotes[selectedChange.id] || ''}
                          onChange={(event) =>
                            setApprovalNotes((current) => ({
                              ...current,
                              [selectedChange.id]: event.target.value,
                            }))
                          }
                        />

                        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                          <Button
                            variant="contained"
                            color="success"
                            size="small"
                            startIcon={<CheckCircleOutlineIcon />}
                            disabled={disabled}
                            onClick={() => onReview?.(selectedChange.id, 'APPROVED', approvalNotes[selectedChange.id] || '')}
                          >
                            Approve
                          </Button>
                          <Button
                            variant="outlined"
                            color="error"
                            size="small"
                            startIcon={<CancelOutlinedIcon />}
                            disabled={disabled}
                            onClick={() => onReview?.(selectedChange.id, 'REJECTED', approvalNotes[selectedChange.id] || '')}
                          >
                            Reject
                          </Button>
                          <Button
                            variant="outlined"
                            color="warning"
                            size="small"
                            startIcon={<ReplyOutlinedIcon />}
                            disabled={disabled}
                            onClick={() => onReview?.(selectedChange.id, 'SENT_BACK', approvalNotes[selectedChange.id] || '')}
                          >
                            Send Back
                          </Button>
                          <Button
                            variant="outlined"
                            color="primary"
                            size="small"
                            startIcon={<DoneAllOutlinedIcon />}
                            disabled={disabled}
                            onClick={() => onReview?.(selectedChange.id, 'RESOLVED', approvalNotes[selectedChange.id] || '')}
                          >
                            Resolve
                          </Button>
                          <IconButton size="small" disabled={disabled} onClick={() => onReview?.(selectedChange.id, 'PENDING', approvalNotes[selectedChange.id] || '')}>
                            <UndoIcon fontSize="small" />
                          </IconButton>
                          <Chip size="small" variant="outlined" label="Reply" />
                          <Chip size="small" variant="outlined" label="History" />
                        </Stack>
                      </>
                    ) : selectedChange.review_comment ? (
                      <Box sx={{ p: 0.75, borderRadius: 0.75, bgcolor: '#eff6ff', border: '1px solid #bfdbfe' }}>
                        <Typography variant="caption" sx={{ fontWeight: 700, display: 'block' }}>
                          Reviewer Note
                        </Typography>
                        <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                          {selectedChange.review_comment}
                        </Typography>
                      </Box>
                    ) : null}
                  </Stack>
                </Paper>
              );
            })()}
          </Box>
        ) : null}
      </Box>
    </>
  );
}
