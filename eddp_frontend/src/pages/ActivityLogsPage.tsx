import BoltOutlinedIcon from '@mui/icons-material/BoltOutlined';
import { Alert, Pagination, Paper, Stack, Typography } from '@mui/material';
import { useMemo } from 'react';

import { EmptyState } from '../components/common/EmptyState';
import { PageHeader } from '../components/common/PageHeader';
import { SearchBar } from '../components/forms/SearchBar';
import { DataTable } from '../components/tables/DataTable';
import { useActivityLogs } from '../features/governance/hooks/useGovernance';
import { applyListQuery } from '../features/shared/filtering';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import { setPage, setSearch } from '../store/slices/activityLogsSlice';

export function ActivityLogsPage() {
  const dispatch = useAppDispatch();
  const query = useAppSelector((state) => state.activityLogs.query);
  const { data = [], isLoading, error } = useActivityLogs();

  const paged = useMemo(
    () =>
      applyListQuery(data, query, {
        statusSelector: (row) => row.status,
        searchSelector: (row) => [row.code, row.module, row.activity, row.reference_number, row.description],
      }),
    [data, query],
  );

  const pageCount = Math.max(1, Math.ceil(paged.total / paged.pageSize));

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Activity Logs"
        subtitle="Operational activity timeline across runtime and governance modules."
      />

      {error ? <Alert severity="error">Failed to load activity logs.</Alert> : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <SearchBar
          value={query.search}
          onChange={(value) => dispatch(setSearch(value))}
          placeholder="Search module, activity, reference"
        />
      </Paper>

      <Paper variant="outlined" sx={{ p: 2 }}>
        {isLoading ? (
          <Typography color="text.secondary">Loading activity logs...</Typography>
        ) : paged.rows.length === 0 ? (
          <EmptyState
            icon={<BoltOutlinedIcon color="disabled" />}
            title="No activity logs"
            description="No activity logs are available for the current filters."
          />
        ) : (
          <DataTable
            rows={paged.rows}
            columns={[
              { key: 'code', header: 'Code', render: (row) => row.code },
              { key: 'module', header: 'Module', render: (row) => row.module },
              { key: 'activity', header: 'Activity', render: (row) => row.activity },
              { key: 'reference', header: 'Reference', render: (row) => row.reference_number || '-' },
              { key: 'status', header: 'Status', render: (row) => row.status },
              { key: 'time', header: 'Activity Time', render: (row) => row.activity_time },
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
