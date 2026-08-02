import GroupOutlinedIcon from '@mui/icons-material/GroupOutlined';
import { Alert, MenuItem, Pagination, Paper, Select, Stack, Typography } from '@mui/material';
import { useMemo } from 'react';

import { EmptyState } from '../components/common/EmptyState';
import { PageHeader } from '../components/common/PageHeader';
import { SearchBar } from '../components/forms/SearchBar';
import { DataTable } from '../components/tables/DataTable';
import type { EntityStatus } from '../features/shared/types';
import { useUsers } from '../features/admin/hooks/useAdmin';
import { STATUS_OPTIONS } from '../features/shared/constants';
import { applyListQuery } from '../features/shared/filtering';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import { setPage, setPageSize, setSearch, setStatus } from '../store/slices/usersSlice';

export function UserManagementPage() {
  const dispatch = useAppDispatch();
  const query = useAppSelector((state) => state.users.query);
  const { data = [], isLoading, error } = useUsers();

  const normalizedRows = useMemo(
    () =>
      data.map((item) => ({
        ...item,
        status: (item.is_active ? 'ACTIVE' : 'INACTIVE') as EntityStatus,
      })),
    [data],
  );

  const paged = useMemo(
    () =>
      applyListQuery(normalizedRows, query, {
        statusSelector: (row) => row.status,
        searchSelector: (row) => [
          row.username,
          row.first_name,
          row.last_name,
          row.email,
          row.roles.join(', '),
        ],
      }),
    [normalizedRows, query],
  );

  const pageCount = Math.max(1, Math.ceil(paged.total / paged.pageSize));

  return (
    <Stack spacing={3}>
      <PageHeader title="User Management" subtitle="Enterprise user administration, directory visibility, and access posture." />

      {error ? <Alert severity="error">Failed to load users.</Alert> : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <SearchBar
            value={query.search}
            onChange={(value) => dispatch(setSearch(value))}
            placeholder="Search username, name, email, role"
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
          <Typography color="text.secondary">Loading users...</Typography>
        ) : paged.rows.length === 0 ? (
          <EmptyState
            icon={<GroupOutlinedIcon color="disabled" />}
            title="No users available"
            description="No users are available for the current filters."
          />
        ) : (
          <DataTable
            rows={paged.rows}
            columns={[
              { key: 'username', header: 'Username', render: (row) => row.username },
              { key: 'name', header: 'Name', render: (row) => `${row.first_name} ${row.last_name}`.trim() || '-' },
              { key: 'email', header: 'Email', render: (row) => row.email || '-' },
              { key: 'roles', header: 'Roles', render: (row) => row.roles.join(', ') || '-' },
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
