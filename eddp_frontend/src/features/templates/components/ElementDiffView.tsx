import {
  Box,
  Card,
  CardContent,
  Chip,
  Typography,
  Stack,
  Button,
  Divider,
  IconButton,
  Tooltip,
  Alert,
  TextField,
} from '@mui/material';
import CheckCircleOutlineIcon from '@mui/icons-material/CheckCircleOutline';
import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined';
import UndoIcon from '@mui/icons-material/Undo';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import DeleteOutlineIcon from '@mui/icons-material/DeleteOutline';
import { useMemo, useState } from 'react';

import type { ElementChange, ChangeType, ApprovalStatus, ReviewAction } from '../types';

interface ElementDiffViewProps {
  change: ElementChange;
  onReview: (changeId: string, action: ReviewAction, comment?: string) => void;
  disabled?: boolean;
}

export function ElementDiffView({ change, onReview, disabled = false }: ElementDiffViewProps) {
  const [approvalNote, setApprovalNote] = useState('');

  type ChangeFacet = 'TYPE' | 'VALUE' | 'POSITION' | 'SIZE' | 'STYLE';

  const STYLE_KEYS = [
    'fontSize',
    'fontWeight',
    'fontStyle',
    'textDecoration',
    'color',
    'backgroundColor',
    'align',
    'opacity',
    'rotation',
  ];

  const readFromPmNode = (node: any): string => {
    if (!node || typeof node !== 'object') {
      return '';
    }

    const parts: string[] = [];
    if (typeof node.text === 'string' && node.text.trim()) {
      parts.push(node.text.trim());
    }

    const attrs = typeof node.attrs === 'object' && node.attrs !== null ? node.attrs : {};
    const binding = (attrs as Record<string, unknown>).binding;
    if (typeof binding === 'string' && binding.trim()) {
      parts.push(`{{${binding.trim()}}}`);
    }

    if (Array.isArray(node.content)) {
      node.content.forEach((child: any) => {
        const childText = readFromPmNode(child);
        if (childText) {
          parts.push(childText);
        }
      });
    }

    return parts.join(' ').replace(/\s+/g, ' ').trim();
  };

  const resolvePrimaryText = (value: any): string => {
    if (!value) {
      return '';
    }
    if (typeof value === 'string') {
      return value;
    }
    if (typeof value === 'object') {
      for (const key of ['newText', 'oldText', 'text', 'content', 'label']) {
        const candidate = value[key as keyof typeof value];
        if (typeof candidate === 'string' && candidate.trim()) {
          return candidate.trim().slice(0, 240);
        }
      }
      const pmText = readFromPmNode(value);
      if (pmText) {
        return pmText.slice(0, 240);
      }
    }
    return '';
  };

  const getComparable = (value: any): Record<string, any> => {
    if (!value || typeof value !== 'object') {
      return {};
    }
    return value;
  };

  const detectFacets = (): ChangeFacet[] => {
    if (change.change_type !== 'MODIFIED') {
      return [];
    }

    const oldObj = getComparable(change.old_value);
    const newObj = getComparable(change.new_value);
    const facets: ChangeFacet[] = [];

    if ((oldObj.type ?? '') !== (newObj.type ?? '')) {
      facets.push('TYPE');
    }

    const oldPrimary = resolvePrimaryText(change.old_value);
    const newPrimary = resolvePrimaryText(change.new_value);
    if (
      oldPrimary !== newPrimary ||
      (oldObj.binding ?? '') !== (newObj.binding ?? '')
    ) {
      facets.push('VALUE');
    }

    if (
      oldObj.page !== newObj.page ||
      oldObj.x !== newObj.x ||
      oldObj.y !== newObj.y
    ) {
      facets.push('POSITION');
    }

    if (oldObj.width !== newObj.width || oldObj.height !== newObj.height) {
      facets.push('SIZE');
    }

    const styleChanged = STYLE_KEYS.some((key) => oldObj[key] !== newObj[key]);
    if (styleChanged) {
      facets.push('STYLE');
    }

    return facets;
  };

  const changeFacets = useMemo(detectFacets, [change]);

  const toFriendlyLines = (value: any): string[] => {
    if (!value || typeof value !== 'object') {
      return [String(value ?? 'None')];
    }

    const lines: string[] = [];

    if (typeof value.newText === 'string' && value.newText.trim()) {
      lines.push(`Text: ${value.newText.trim()}`);
    } else if (typeof value.oldText === 'string' && value.oldText.trim()) {
      lines.push(`Text: ${value.oldText.trim()}`);
    } else {
      const pmText = readFromPmNode(value);
      if (pmText) {
        lines.push(`Text: ${pmText.slice(0, 280)}${pmText.length > 280 ? '...' : ''}`);
      }
    }

    if (value.type) lines.push(`Type: ${value.type}`);
    if (value.label) lines.push(`Label: ${value.label}`);
    if (value.text) lines.push(`Text: ${value.text}`);
    if (value.binding) lines.push(`Binding: ${value.binding}`);
    if (typeof value.x === 'number' && typeof value.y === 'number') lines.push(`Position: ${value.x}, ${value.y}`);
    if (typeof value.width === 'number' && typeof value.height === 'number') lines.push(`Size: ${value.width} x ${value.height}`);

    if (lines.length === 0) {
      lines.push(JSON.stringify(value));
    }

    return lines;
  };

  const getChangeColor = (changeType: ChangeType): string => {
    switch (changeType) {
      case 'ADDED':
        return '#f59e0b'; // Yellow/Amber
      case 'MODIFIED':
        return '#f59e0b'; // Yellow/Amber
      case 'DELETED':
        return '#f44336'; // Red
      default:
        return '#9e9e9e';
    }
  };

  const getChangeIcon = (changeType: ChangeType) => {
    switch (changeType) {
      case 'ADDED':
        return <AddCircleOutlineIcon sx={{ color: getChangeColor(changeType) }} />;
      case 'MODIFIED':
        return <EditOutlinedIcon sx={{ color: getChangeColor(changeType) }} />;
      case 'DELETED':
        return <DeleteOutlineIcon sx={{ color: getChangeColor(changeType) }} />;
      default:
        return null;
    }
  };

  const getStatusChip = (status: ApprovalStatus) => {
    const statusConfig: Record<ApprovalStatus, { label: string; color: 'warning' | 'success' | 'error' | 'default' }> = {
      PENDING: { label: 'Pending Review', color: 'warning' as const },
      APPROVED: { label: 'Approved', color: 'success' as const },
      REJECTED: { label: 'Rejected', color: 'error' as const },
      REVERTED: { label: 'Reverted', color: 'default' as const },
      SENT_BACK: { label: 'Sent Back', color: 'warning' as const },
      RESOLVED: { label: 'Resolved', color: 'success' as const },
    };
    const config = statusConfig[status];
    return <Chip label={config.label} color={config.color} size="small" />;
  };

  const facetColor = (facet: ChangeFacet) => {
    switch (facet) {
      case 'VALUE':
        return 'warning';
      case 'POSITION':
      case 'SIZE':
        return 'info';
      case 'STYLE':
        return 'secondary';
      case 'TYPE':
        return 'default';
      default:
        return 'default';
    }
  };

  const renderValue = (value: any, displayMode: 'added' | 'removed' | 'modified') => {
    if (!value) return <Typography variant="body2" color="text.secondary">None</Typography>;

    const isRemoved = displayMode === 'removed';
    const isAdded = displayMode === 'added';
    const isModified = displayMode === 'modified';

    const background = isAdded
      ? 'rgba(34, 197, 94, 0.10)'
      : isRemoved
        ? 'rgba(239, 68, 68, 0.10)'
        : 'rgba(245, 158, 11, 0.14)';
    const border = isAdded
      ? 'rgba(34, 197, 94, 0.45)'
      : isRemoved
        ? 'rgba(239, 68, 68, 0.45)'
        : 'rgba(245, 158, 11, 0.55)';
    const textColor = isRemoved ? '#b91c1c' : isAdded ? '#166534' : '#7c2d12';

    return (
      <Box
        sx={{
          p: 1.5,
          borderRadius: 1,
          bgcolor: background,
          border: `1px solid ${border}`,
          textDecoration: isRemoved ? 'line-through' : 'none',
          opacity: isRemoved ? 0.9 : 1,
          color: textColor,
        }}
      >
        <Stack spacing={0.5}>
          <Chip
            size="small"
            label={isAdded ? 'Added in this version' : isRemoved ? 'Removed from previous version' : isModified ? 'Modified value' : 'Change'}
            sx={{ alignSelf: 'flex-start', mb: 0.5 }}
            color={isAdded ? 'success' : isRemoved ? 'error' : 'warning'}
          />
          {toFriendlyLines(value).map((line, index) => (
            <Typography key={index} variant="body2">
              {line}
            </Typography>
          ))}
        </Stack>
      </Box>
    );
  };

  const isPending = change.approval_status === 'PENDING';

  return (
    <Card
      sx={{
        mb: 2,
        borderLeft: `4px solid ${getChangeColor(change.change_type)}`,
        bgcolor: change.approval_status === 'REJECTED' ? 'rgba(244, 67, 54, 0.02)' : 'background.paper',
      }}
    >
      <CardContent>
        <Stack spacing={2}>
          {/* Header */}
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <Stack direction="row" spacing={1} alignItems="center">
              {getChangeIcon(change.change_type)}
              <Typography variant="subtitle1" fontWeight="medium">
                {change.change_type} • {change.element_id}
              </Typography>
            </Stack>
            {getStatusChip(change.approval_status)}
          </Box>

          <Stack direction="row" spacing={0.75} flexWrap="wrap" useFlexGap>
            <Chip size="small" label={`Change Type: ${change.change_type}`} variant="outlined" />
            {changeFacets.map((facet) => (
              <Chip key={facet} size="small" label={facet} color={facetColor(facet)} variant="outlined" />
            ))}
          </Stack>

          <Divider />

          {/* Content comparison */}
          {change.change_type === 'ADDED' && (
            <Box>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                New Content:
              </Typography>
              {renderValue(change.new_value, 'added')}
              {resolvePrimaryText(change.new_value) && (
                <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems={{ xs: 'stretch', md: 'center' }} sx={{ mt: 1 }}>
                  <Typography variant="body2" sx={{ px: 0.75, py: 0.25, bgcolor: '#fff59d', borderRadius: 0.5, fontWeight: 600 }}>
                    {resolvePrimaryText(change.new_value)}
                  </Typography>
                  <TextField
                    size="small"
                    label="Approval note"
                    placeholder="Add note for this change"
                    value={approvalNote}
                    onChange={(event) => setApprovalNote(event.target.value)}
                    sx={{ minWidth: 280 }}
                  />
                </Stack>
              )}
            </Box>
          )}

          {change.change_type === 'DELETED' && (
            <Box>
              <Typography variant="caption" color="text.secondary" gutterBottom>
                Previous Content (Removed in this version):
              </Typography>
              {renderValue(change.old_value, 'removed')}
            </Box>
          )}

          {change.change_type === 'MODIFIED' && (
            <Stack spacing={2}>
              <Box>
                <Typography variant="caption" color="text.secondary" gutterBottom>
                  Previous Value (v1):
                </Typography>
                {renderValue(change.old_value, 'removed')}
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary" gutterBottom>
                  New Value (v2):
                </Typography>
                {renderValue(change.new_value, 'added')}
                {resolvePrimaryText(change.new_value) && (
                  <Stack direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems={{ xs: 'stretch', md: 'center' }} sx={{ mt: 1 }}>
                    <Typography variant="body2" sx={{ px: 0.75, py: 0.25, bgcolor: '#ffedd5', borderRadius: 0.5, fontWeight: 600, color: '#9a3412' }}>
                      Modified content highlighted (amber)
                    </Typography>
                    <TextField
                      size="small"
                      label="Approval note"
                      placeholder="Add note for this change"
                      value={approvalNote}
                      onChange={(event) => setApprovalNote(event.target.value)}
                      sx={{ minWidth: 280 }}
                    />
                  </Stack>
                )}
              </Box>
            </Stack>
          )}

          {/* Review comment */}
          {change.review_comment && (
            <Alert severity="info" sx={{ mt: 1 }}>
              <Typography variant="body2">
                <strong>Comment:</strong> {change.review_comment}
              </Typography>
              {change.reviewed_by_name && (
                <Typography variant="caption" color="text.secondary">
                  — {change.reviewed_by_name} at {new Date(change.reviewed_at!).toLocaleString()}
                </Typography>
              )}
            </Alert>
          )}

          {/* Action buttons */}
          {isPending && (
            <Stack direction="row" spacing={1} justifyContent="flex-end">
              <Tooltip title="Approve this change">
                <Button
                  variant="contained"
                  color="success"
                  size="small"
                  startIcon={<CheckCircleOutlineIcon />}
                  onClick={() => onReview(change.id, 'APPROVED', approvalNote)}
                  disabled={disabled}
                >
                  Approve
                </Button>
              </Tooltip>
              <Tooltip title="Reject this change">
                <Button
                  variant="outlined"
                  color="error"
                  size="small"
                  startIcon={<CancelOutlinedIcon />}
                  onClick={() => onReview(change.id, 'REJECTED', approvalNote)}
                  disabled={disabled}
                >
                  Reject
                </Button>
              </Tooltip>
              <Tooltip title="Revert to original">
                <IconButton
                  size="small"
                  onClick={() => onReview(change.id, 'REVERTED', approvalNote)}
                  disabled={disabled}
                >
                  <UndoIcon />
                </IconButton>
              </Tooltip>
            </Stack>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}
