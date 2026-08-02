import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import DeleteOutlineOutlinedIcon from '@mui/icons-material/DeleteOutlineOutlined';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import VisibilityOutlinedIcon from '@mui/icons-material/VisibilityOutlined';
import RefreshIcon from '@mui/icons-material/Refresh';
import PictureAsPdfOutlinedIcon from '@mui/icons-material/PictureAsPdfOutlined';
import {
  Alert,
  Button,
  Chip,
  IconButton,
  MenuItem,
  Pagination,
  Paper,
  Select,
  Stack,
  Typography,
  Tooltip,
} from '@mui/material';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { ConfirmDialog } from '../components/dialogs/ConfirmDialog';
import { SearchBar } from '../components/forms/SearchBar';
import { PageHeader } from '../components/common/PageHeader';
import { DataTable } from '../components/tables/DataTable';
import { TEMPLATE_ROUTES } from '../constants/appConstants';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';
import {
  setPage,
  setPageSize,
  setSearch,
  setStatus,
} from '../store/slices/templatesSlice';
import { STATUS_OPTIONS } from '../features/shared/constants';
import { applyListQuery } from '../features/shared/filtering';
import { useDeleteDraftVersion, useDeleteTemplate, useTemplates } from '../features/templates/hooks/useTemplates';
import type { TemplateItem } from '../features/templates/types';

type TemplateListRow = TemplateItem & {
  row_kind: 'BASE' | 'PENDING_DRAFT';
  source_template_id: string;
};

export function TemplatesListPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const query = useAppSelector((state) => state.templates.query);
  const { data = [], isLoading, error, refetch } = useTemplates();
  const deleteMutation = useDeleteTemplate();
  const deleteDraftVersionMutation = useDeleteDraftVersion();

  const [pendingDelete, setPendingDelete] = useState<TemplateListRow | null>(null);

  const listRows = useMemo<TemplateListRow[]>(() => {
    return data.flatMap((template) => {
      const baseRow: TemplateListRow = {
        ...template,
        row_kind: 'BASE',
        source_template_id: template.id,
      };

      if (!template.has_pending_draft || !template.pending_draft_version || (template.version_count ?? 0) < 1) {
        return [baseRow];
      }

      const draftRow: TemplateListRow = {
        ...template,
        row_kind: 'PENDING_DRAFT',
        source_template_id: template.id,
        status: template.pending_draft_status === 'FOR_REVIEW' ? 'FOR_REVIEW' : 'DRAFT',
        code: `${template.code}_V${template.pending_draft_version}`,
        name: `${template.name} (v${template.pending_draft_version}.0 ${template.pending_draft_status === 'FOR_REVIEW' ? 'In Review' : 'Draft'})`,
      };

      return [baseRow, draftRow];
    });
  }, [data]);

  const paged = useMemo(
    () =>
      applyListQuery(listRows, query, {
        statusSelector: (row: TemplateListRow) => row.status,
        searchSelector: (row: TemplateListRow) => [row.code, row.name, row.category, row.content_type],
      }),
    [listRows, query],
  );

  const pageCount = Math.max(1, Math.ceil(paged.total / paged.pageSize));

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Document Create or Delete" 
        subtitle="Create, edit, and manage your templates"
        actions={
          <Stack direction="row" spacing={1}>
            <Button variant="outlined" startIcon={<RefreshIcon />} onClick={() => refetch()}>
              Refresh
            </Button>
            <Button variant="contained" startIcon={<AddOutlinedIcon />} onClick={() => navigate(TEMPLATE_ROUTES.CREATE)}>
              Create Template
            </Button>
          </Stack>
        }
      />

      {error ? <Alert severity="error">Failed to load templates.</Alert> : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <SearchBar
            value={query.search}
            onChange={(value) => dispatch(setSearch(value))}
            placeholder="Search by code, name, category"
          />
          <Select
            size="small"
            value={query.status}
            onChange={(event) => dispatch(setStatus(event.target.value as typeof query.status))}
            displayEmpty
            sx={{ minWidth: 180 }}
          >
            <MenuItem value="">All Statuses</MenuItem>
            {STATUS_OPTIONS.map((status) => (
              <MenuItem key={status} value={status}>
                {status}
              </MenuItem>
            ))}
          </Select>
          <Select
            size="small"
            value={String(query.pageSize)}
            onChange={(event) => dispatch(setPageSize(Number(event.target.value)))}
            sx={{ minWidth: 120 }}
          >
            {[10, 20, 50].map((size) => (
              <MenuItem key={size} value={String(size)}>
                {size} / page
              </MenuItem>
            ))}
          </Select>
        </Stack>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <DataTable
          rows={paged.rows}
          emptyMessage={isLoading ? 'Loading templates...' : 'No templates found.'}
          columns={[
            { key: 'code', header: 'Code', render: (row: TemplateItem) => row.code },
            { key: 'name', header: 'Name', render: (row: TemplateItem) => row.name },
            { key: 'category', header: 'Category', render: (row: TemplateItem) => row.category },
            { key: 'type', header: 'Template Type', render: (row: TemplateItem) => row.template_type },
            { 
              key: 'status', 
              header: 'Status', 
              render: (row: TemplateListRow) => {
                const statusConfig = {
                  DRAFT: { label: 'Draft', color: 'default' as const },
                  FOR_REVIEW: { label: 'For Review', color: 'warning' as const },
                  APPROVED: { label: 'Approved', color: 'success' as const },
                  ARCHIVED: { label: 'Archived', color: 'default' as const },
                };
                const config = statusConfig[row.status] || { label: row.status, color: 'default' as const };
                return (
                  <Stack direction="row" spacing={0.5} alignItems="center">
                    <Chip label={config.label} color={config.color} size="small" />
                    {row.row_kind === 'PENDING_DRAFT' && row.pending_draft_version && (
                      <Chip 
                        label={`v${row.pending_draft_version}.0 ${row.status === 'FOR_REVIEW' ? 'In Review' : 'Draft Pending'}`} 
                        color="warning" 
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </Stack>
                );
              }
            },
            {
              key: 'actions',
              header: 'Actions',
              render: (row: TemplateListRow) => (
                <Stack direction="row" spacing={1}>
                  {(() => {
                    const pendingVersion = row.pending_draft_version;
                    if (row.row_kind !== 'PENDING_DRAFT' || pendingVersion == null) {
                      return null;
                    }
                    return (
                    <Tooltip title={row.status === 'FOR_REVIEW' ? 'Open In-Review Version' : 'Edit Draft Version'}>
                      <IconButton 
                        onClick={() => navigate(TEMPLATE_ROUTES.editVersion(row.source_template_id, pendingVersion))}
                        color="warning"
                      >
                        <EditOutlinedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    );
                  })()}
                  <Tooltip title="View">
                    <IconButton onClick={() => navigate(TEMPLATE_ROUTES.view(row.source_template_id))}>
                      <VisibilityOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  {row.status === 'APPROVED' && row.row_kind === 'BASE' ? (
                    <Tooltip title="Open PDF Studio">
                      <IconButton onClick={() => navigate(TEMPLATE_ROUTES.pdfStudio(row.source_template_id))}>
                        <PictureAsPdfOutlinedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  ) : null}
                  {row.row_kind === 'BASE' && (
                    <>
                      <Tooltip
                        title={
                          row.has_pending_draft && row.pending_draft_version
                            ? `Continue Draft v${row.pending_draft_version}.0`
                            : 'Edit'
                        }
                      >
                        <IconButton
                          onClick={() => {
                            if (row.has_pending_draft && row.pending_draft_version) {
                              navigate(TEMPLATE_ROUTES.editVersion(row.source_template_id, row.pending_draft_version));
                              return;
                            }
                            navigate(TEMPLATE_ROUTES.edit(row.source_template_id));
                          }}
                        >
                          <EditOutlinedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete">
                        <IconButton onClick={() => setPendingDelete(row)}>
                          <DeleteOutlineOutlinedIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </>
                  )}
                  {row.row_kind === 'PENDING_DRAFT' && row.pending_draft_version && (
                    <Tooltip title="Delete Draft Version">
                      <IconButton onClick={() => setPendingDelete(row)} color="error">
                        <DeleteOutlineOutlinedIcon fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  )}
                </Stack>
              ),
            },
          ]}
        />

        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {paged.total} record(s)
          </Typography>
          <Pagination
            page={query.page}
            count={pageCount}
            onChange={(_, page) => dispatch(setPage(page))}
            color="primary"
          />
        </Stack>
      </Paper>

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title={pendingDelete?.row_kind === 'PENDING_DRAFT' ? 'Delete Draft Version' : 'Delete Template'}
        description={
          pendingDelete?.row_kind === 'PENDING_DRAFT'
            ? `Delete pending draft ${pendingDelete?.pending_draft_version ? `v${pendingDelete.pending_draft_version}.0` : ''} for ${pendingDelete?.name ?? 'this template'}?`
            : `Delete ${pendingDelete?.name ?? 'this template'}?`
        }
        onCancel={() => setPendingDelete(null)}
        onConfirm={async () => {
          if (!pendingDelete) {
            return;
          }
          if (pendingDelete.row_kind === 'PENDING_DRAFT' && pendingDelete.pending_draft_version) {
            await deleteDraftVersionMutation.mutateAsync({
              templateId: pendingDelete.source_template_id,
              versionNumber: pendingDelete.pending_draft_version,
            });
            dispatch(enqueueNotification({ severity: 'success', message: `Draft version v${pendingDelete.pending_draft_version}.0 deleted.` }));
          } else {
            await deleteMutation.mutateAsync(pendingDelete.id);
            dispatch(enqueueNotification({ severity: 'success', message: 'Template deleted.' }));
          }
          setPendingDelete(null);
        }}
      />
    </Stack>
  );
}
