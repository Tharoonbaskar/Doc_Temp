import ReceiptLongOutlinedIcon from '@mui/icons-material/ReceiptLongOutlined';
import { Alert, Pagination, Paper, Stack, Typography } from '@mui/material';
import { useMemo } from 'react';

import { EmptyState } from '../components/common/EmptyState';
import { PageHeader } from '../components/common/PageHeader';
import { SearchBar } from '../components/forms/SearchBar';
import { DataTable } from '../components/tables/DataTable';
import { useAuditLogs } from '../features/governance/hooks/useGovernance';
import { applyListQuery } from '../features/shared/filtering';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import { setPage, setSearch } from '../store/slices/auditLogsSlice';

export function AuditLogsPage() {
  const dispatch = useAppDispatch();
  const query = useAppSelector((state) => state.auditLogs.query);
  const { data = [], isLoading, error } = useAuditLogs();

  const paged = useMemo(
    () =>
      applyListQuery(data, query, {
        statusSelector: (row) => row.status,
        searchSelector: (row) => [row.code, row.entity_name, row.entity_id, row.action, row.performed_by?.username ?? ''],
      }),
    [data, query],
  );

  const pageCount = Math.max(1, Math.ceil(paged.total / paged.pageSize));

  return (
    <Stack spacing={3}>
      <PageHeader title="Audit Logs" subtitle="Entity-level audit trail with action timeline for governance and compliance." />

      {error ? <Alert severity="error">Failed to load audit logs.</Alert> : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <SearchBar
          value={query.search}
          onChange={(value) => dispatch(setSearch(value))}
          placeholder="Search action, entity, user"
        />
      </Paper>

      <Paper variant="outlined" sx={{ p: 2 }}>
        {isLoading ? (
          <Typography color="text.secondary">Loading audit logs...</Typography>
        ) : paged.rows.length === 0 ? (
          <EmptyState
            icon={<ReceiptLongOutlinedIcon color="disabled" />}
            title="No audit logs"
            description="No audit log data returned from governance endpoints."
          />
        ) : (
          <DataTable
            rows={paged.rows}
            columns={[
              { key: 'code', header: 'Code', render: (row) => row.code },
              { key: 'entity', header: 'Entity', render: (row) => `${row.entity_name}:${row.entity_id}` },
              { key: 'action', header: 'Action', render: (row) => row.action },
              { key: 'status', header: 'Status', render: (row) => row.status },
              { key: 'user', header: 'User', render: (row) => row.performed_by?.username ?? '-' },
              { key: 'time', header: 'Created On', render: (row) => row.created_on },
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
