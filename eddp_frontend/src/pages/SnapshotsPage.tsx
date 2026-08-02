import HistoryOutlinedIcon from '@mui/icons-material/HistoryOutlined';
import { Alert, Pagination, Paper, Stack, Typography } from '@mui/material';
import { useMemo } from 'react';

import { EmptyState } from '../components/common/EmptyState';
import { PageHeader } from '../components/common/PageHeader';
import { SearchBar } from '../components/forms/SearchBar';
import { DataTable } from '../components/tables/DataTable';
import { useSnapshots } from '../features/governance/hooks/useGovernance';
import { applyListQuery } from '../features/shared/filtering';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import { setPage, setSearch } from '../store/slices/snapshotsSlice';

export function SnapshotsPage() {
  const dispatch = useAppDispatch();
  const query = useAppSelector((state) => state.snapshots.query);
  const { data = [], isLoading, error } = useSnapshots();

  const paged = useMemo(
    () =>
      applyListQuery(data, query, {
        statusSelector: (row) => row.status,
        searchSelector: (row) => [
          row.code,
          row.generated_document?.code ?? '',
          row.generated_document?.file_name ?? '',
          String(row.snapshot_version),
        ],
      }),
    [data, query],
  );

  const pageCount = Math.max(1, Math.ceil(paged.total / paged.pageSize));

  return (
    <Stack spacing={3}>
      <PageHeader title="Snapshots" subtitle="Snapshot timeline and version trail for generated document states." />

      {error ? <Alert severity="error">Failed to load snapshots.</Alert> : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <SearchBar
          value={query.search}
          onChange={(value) => dispatch(setSearch(value))}
          placeholder="Search snapshot code, document code, file"
        />
      </Paper>

      <Paper variant="outlined" sx={{ p: 2 }}>
        {isLoading ? (
          <Typography color="text.secondary">Loading snapshots...</Typography>
        ) : paged.rows.length === 0 ? (
          <EmptyState
            icon={<HistoryOutlinedIcon color="disabled" />}
            title="No snapshots"
            description="No snapshots are available for the current filters."
          />
        ) : (
          <DataTable
            rows={paged.rows}
            columns={[
              { key: 'code', header: 'Code', render: (row) => row.code },
              { key: 'document', header: 'Document', render: (row) => row.generated_document?.file_name ?? '-' },
              { key: 'version', header: 'Snapshot Version', render: (row) => row.snapshot_version },
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
