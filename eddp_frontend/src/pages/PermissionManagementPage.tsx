import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import { Alert, MenuItem, Pagination, Paper, Select, Stack, Typography } from '@mui/material';
import { useMemo } from 'react';

import { EmptyState } from '../components/common/EmptyState';
import { PageHeader } from '../components/common/PageHeader';
import { SearchBar } from '../components/forms/SearchBar';
import { DataTable } from '../components/tables/DataTable';
import { usePermissions } from '../features/admin/hooks/useAdmin';
import { STATUS_OPTIONS } from '../features/shared/constants';
import { applyListQuery } from '../features/shared/filtering';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import { setPage, setPageSize, setSearch, setStatus } from '../store/slices/permissionsSlice';

export function PermissionManagementPage() {
  const dispatch = useAppDispatch();
  const query = useAppSelector((state) => state.permissions.query);
  const { data = [], isLoading, error } = usePermissions();

  const paged = useMemo(
    () =>
      applyListQuery(data, query, {
        statusSelector: (row) => row.status,
        searchSelector: (row) => [row.code, row.module, row.action, row.description],
      }),
    [data, query],
  );

  const pageCount = Math.max(1, Math.ceil(paged.total / paged.pageSize));

  return (
    <Stack spacing={3}>
      <PageHeader title="Permission Management" subtitle="Manage module-action permission matrix and enterprise access controls." />

      {error ? <Alert severity="error">Failed to load permissions.</Alert> : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <SearchBar
            value={query.search}
            onChange={(value) => dispatch(setSearch(value))}
            placeholder="Search code, module, action"
          />
          <Select
            size="small"
            value={query.status}
            onChange={(event) => dispatch(setStatus(event.target.value as typeof query.status))}
            displayEmpty
            sx={{ minWidth: 180 }}
          >
            <MenuItem value="">All Statuses</MenuItem>
            {STATUS_OPTIONS.map((item) => (
              <MenuItem key={item} value={item}>
                {item}
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
        {isLoading ? (
          <Typography color="text.secondary">Loading permissions...</Typography>
        ) : paged.rows.length === 0 ? (
          <EmptyState
            icon={<LockOutlinedIcon color="disabled" />}
            title="No permissions available"
            description="No permissions are available for the current filters."
          />
        ) : (
          <DataTable
            rows={paged.rows}
            columns={[
              { key: 'code', header: 'Code', render: (row) => row.code },
              { key: 'module', header: 'Module', render: (row) => row.module },
              { key: 'action', header: 'Action', render: (row) => row.action },
              { key: 'description', header: 'Description', render: (row) => row.description || '-' },
              { key: 'status', header: 'Status', render: (row) => row.status },
            ]}
          />
        )}

        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" sx={{ mt: 2 }}>
          <Typography variant="body2" color="text.secondary">
            {paged.total} record(s)
          </Typography>
          <Pagination page={query.page} count={pageCount} onChange={(_, page) => dispatch(setPage(page))} color="primary" />
        </Stack>
      </Paper>
    </Stack>
  );
}
