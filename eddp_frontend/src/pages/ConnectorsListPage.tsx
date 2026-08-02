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
import { CONNECTOR_ROUTES } from '../constants/appConstants';
import { useDeleteConnector, useConnectors } from '../features/connectors/hooks/useConnectors';
import type { ConnectorItem } from '../features/connectors/types';
import { STATUS_OPTIONS } from '../features/shared/constants';
import { applyListQuery } from '../features/shared/filtering';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';
import { setPage, setPageSize, setSearch, setStatus } from '../store/slices/connectorsSlice';

export function ConnectorsListPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const query = useAppSelector((state) => state.connectors.query);
  const { data = [], isLoading, error } = useConnectors();
  const deleteMutation = useDeleteConnector();

  const [pendingDelete, setPendingDelete] = useState<ConnectorItem | null>(null);

  const paged = useMemo(
    () =>
      applyListQuery(data, query, {
        statusSelector: (row) => row.status,
        searchSelector: (row) => [row.code, row.name, row.connector_type, row.host, row.api_base_url],
      }),
    [data, query],
  );

  const pageCount = Math.max(1, Math.ceil(paged.total / paged.pageSize));

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Connectors"
        subtitle="Manage external integration connectors and settings."
        actions={
          <Button variant="contained" startIcon={<AddOutlinedIcon />} onClick={() => navigate(CONNECTOR_ROUTES.CREATE)}>
            Create Connector
          </Button>
        }
      />

      {error ? <Alert severity="error">Failed to load connectors.</Alert> : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <SearchBar value={query.search} onChange={(value) => dispatch(setSearch(value))} placeholder="Search connectors" />
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
          emptyMessage={isLoading ? 'Loading connectors...' : 'No connectors found.'}
          columns={[
            { key: 'code', header: 'Code', render: (row) => row.code },
            { key: 'name', header: 'Name', render: (row) => row.name },
            { key: 'type', header: 'Type', render: (row) => row.connector_type },
            { key: 'host', header: 'Host/API', render: (row) => row.host || row.api_base_url || '-' },
            { key: 'active', header: 'Active', render: (row) => (row.is_active ? 'Yes' : 'No') },
            { key: 'status', header: 'Status', render: (row) => row.status },
            {
              key: 'actions',
              header: 'Actions',
              render: (row) => (
                <Stack direction="row" spacing={1}>
                  <IconButton onClick={() => navigate(CONNECTOR_ROUTES.view(row.id))}>
                    <VisibilityOutlinedIcon fontSize="small" />
                  </IconButton>
                  <IconButton onClick={() => navigate(CONNECTOR_ROUTES.edit(row.id))}>
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
        title="Delete Connector"
        description={`Delete ${pendingDelete?.name ?? 'this connector'}?`}
        onCancel={() => setPendingDelete(null)}
        onConfirm={async () => {
          if (!pendingDelete) {
            return;
          }
          await deleteMutation.mutateAsync(pendingDelete.id);
          dispatch(enqueueNotification({ severity: 'success', message: 'Connector deleted.' }));
          setPendingDelete(null);
        }}
      />
    </Stack>
  );
}
