import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import DeleteOutlineOutlinedIcon from '@mui/icons-material/DeleteOutlineOutlined';
import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import VisibilityOutlinedIcon from '@mui/icons-material/VisibilityOutlined';
import {
  Alert,
  Button,
  IconButton,
  MenuItem,
  Pagination,
  Paper,
  Select,
  Stack,
  Typography,
} from '@mui/material';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '../components/common/PageHeader';
import { DataTable } from '../components/tables/DataTable';
import { ConfirmDialog } from '../components/dialogs/ConfirmDialog';
import { SearchBar } from '../components/forms/SearchBar';
import { WORKFLOW_ROUTES } from '../constants/appConstants';
import { useDeleteWorkflow, useWorkflowList } from '../features/workflow/hooks/useWorkflow';
import type { WorkflowItem } from '../features/workflow/types';
import { STATUS_OPTIONS } from '../features/shared/constants';
import { applyListQuery } from '../features/shared/filtering';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';
import { setPage, setPageSize, setSearch, setStatus } from '../store/slices/workflowSlice';

export function WorkflowListPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const query = useAppSelector((state) => state.workflow.query);
  const { data = [], isLoading, error } = useWorkflowList();
  const deleteMutation = useDeleteWorkflow();

  const [pendingDelete, setPendingDelete] = useState<WorkflowItem | null>(null);

  const paged = useMemo(
    () =>
      applyListQuery(data, query, {
        statusSelector: (row) => row.status,
        searchSelector: (row) => [row.code, row.name, row.workflow_type, row.applicable_document?.name ?? ''],
      }),
    [data, query],
  );

  const pageCount = Math.max(1, Math.ceil(paged.total / paged.pageSize));

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Workflow"
        subtitle="Manage workflow definitions and versions."
        actions={
          <Button variant="contained" startIcon={<AddOutlinedIcon />} onClick={() => navigate(WORKFLOW_ROUTES.CREATE)}>
            Create Workflow
          </Button>
        }
      />

      {error ? <Alert severity="error">Failed to load workflows.</Alert> : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <SearchBar value={query.search} onChange={(value) => dispatch(setSearch(value))} placeholder="Search workflows" />
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
          emptyMessage={isLoading ? 'Loading workflows...' : 'No workflows found.'}
          columns={[
            { key: 'code', header: 'Code', render: (row) => row.code },
            { key: 'name', header: 'Name', render: (row) => row.name },
            { key: 'type', header: 'Workflow Type', render: (row) => row.workflow_type },
            { key: 'version', header: 'Version', render: (row) => row.version },
            { key: 'default', header: 'Default', render: (row) => (row.is_default ? 'Yes' : 'No') },
            { key: 'status', header: 'Status', render: (row) => row.status },
            {
              key: 'actions',
              header: 'Actions',
              render: (row) => (
                <Stack direction="row" spacing={1}>
                  <IconButton onClick={() => navigate(WORKFLOW_ROUTES.view(row.id))}>
                    <VisibilityOutlinedIcon fontSize="small" />
                  </IconButton>
                  <IconButton onClick={() => navigate(WORKFLOW_ROUTES.edit(row.id))}>
                    <EditOutlinedIcon fontSize="small" />
                  </IconButton>
                  <IconButton onClick={() => setPendingDelete(row)}>
                    <DeleteOutlineOutlinedIcon fontSize="small" />
                  </IconButton>
                </Stack>
              ),
            },
          ]}
        />

        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary">{paged.total} record(s)</Typography>
          <Pagination page={query.page} count={pageCount} onChange={(_, page) => dispatch(setPage(page))} color="primary" />
        </Stack>
      </Paper>

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        title="Delete Workflow"
        description={`Delete ${pendingDelete?.name ?? 'this workflow'}?`}
        onCancel={() => setPendingDelete(null)}
        onConfirm={async () => {
          if (!pendingDelete) {
            return;
          }
          await deleteMutation.mutateAsync(pendingDelete.id);
          dispatch(enqueueNotification({ severity: 'success', message: 'Workflow deleted.' }));
          setPendingDelete(null);
        }}
      />
    </Stack>
  );
}
