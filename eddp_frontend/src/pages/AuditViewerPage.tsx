import TimelineOutlinedIcon from '@mui/icons-material/TimelineOutlined';
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

export function AuditViewerPage() {
  const dispatch = useAppDispatch();
  const query = useAppSelector((state) => state.auditLogs.query);
  const { data = [], isLoading, error } = useAuditLogs();

  const paged = useMemo(
    () =>
      applyListQuery(data, query, {
        statusSelector: (row) => row.status,
        searchSelector: (row) => [row.entity_name, row.entity_id, row.action, row.code],
      }),
    [data, query],
  );

  const pageCount = Math.max(1, Math.ceil(paged.total / paged.pageSize));

  return (
    <Stack spacing={3}>
      <PageHeader title="Audit Viewer" subtitle="Enterprise audit timeline with entity-level change visibility." />

      {error ? <Alert severity="error">Failed to load audit timeline.</Alert> : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <SearchBar
          value={query.search}
          onChange={(value) => dispatch(setSearch(value))}
          placeholder="Search entity, action, code"
        />
      </Paper>

      <Paper variant="outlined" sx={{ p: 2 }}>
        {isLoading ? (
          <Typography color="text.secondary">Loading audit timeline...</Typography>
        ) : paged.rows.length === 0 ? (
          <EmptyState
            icon={<TimelineOutlinedIcon color="disabled" />}
            title="No audit timeline entries"
            description="Audit logs are currently empty for this environment."
          />
        ) : (
          <DataTable
            rows={paged.rows}
            columns={[
              { key: 'code', header: 'Code', render: (row) => row.code },
              { key: 'entity', header: 'Entity', render: (row) => `${row.entity_name}:${row.entity_id}` },
              { key: 'action', header: 'Action', render: (row) => row.action },
              { key: 'status', header: 'Status', render: (row) => row.status },
              { key: 'created', header: 'Created On', render: (row) => row.created_on },
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
