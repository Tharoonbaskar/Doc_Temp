import CheckCircleOutlineOutlinedIcon from '@mui/icons-material/CheckCircleOutlineOutlined';
import HourglassBottomOutlinedIcon from '@mui/icons-material/HourglassBottomOutlined';
import VisibilityOutlinedIcon from '@mui/icons-material/VisibilityOutlined';
import {
  Alert,
  Button,
  Chip,
  MenuItem,
  Pagination,
  Paper,
  Select,
  Stack,
  Typography,
} from '@mui/material';
import { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { PageHeader } from '../components/common/PageHeader';
import { DataTable } from '../components/tables/DataTable';
import { SearchBar } from '../components/forms/SearchBar';
import { RUNTIME_ROUTES } from '../constants/appConstants';
import { useRuntimeGenerationRequests } from '../features/runtime/hooks/useRuntime';
import { applyListQuery } from '../features/shared/filtering';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import {
  setPage,
  setPageSize,
  setSearch,
  setSelectedCorrelationId,
  setSelectedRequestId,
  setStatus,
} from '../store/slices/runtimeSlice';

const normalizeRequestId = (value: string | null | undefined): string => {
  const normalized = (value ?? '').trim();
  if (!normalized) {
    return '';
  }
  const lowered = normalized.toLowerCase();
  if (lowered === 'undefined' || lowered === 'null') {
    return '';
  }
  return normalized;
};

export function RuntimePage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const query = useAppSelector((state) => state.runtime.query);
  const { data = [], isLoading, error } = useRuntimeGenerationRequests();

  const paged = useMemo(
    () =>
      applyListQuery(data, query, {
        statusSelector: (row) => row.status,
        searchSelector: (row) => [row.code, row.request_id, row.correlation_id ?? row.business_reference, row.request_source],
      }),
    [data, query],
  );

  const pageCount = Math.max(1, Math.ceil(paged.total / paged.pageSize));

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Runtime"
        subtitle="Track generation requests, live status, and handoff to preview and generation flows."
        actions={
          <Stack direction="row" spacing={1}>
            <Button variant="outlined" onClick={() => navigate(RUNTIME_ROUTES.PREVIEW)}>
              Document Preview
            </Button>
            <Button variant="contained" onClick={() => navigate(RUNTIME_ROUTES.GENERATION)}>
              Document Generation
            </Button>
          </Stack>
        }
      />

      {error ? <Alert severity="error">Failed to load runtime requests.</Alert> : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <SearchBar
            value={query.search}
            onChange={(value) => dispatch(setSearch(value))}
            placeholder="Search request ID, correlation ID, source"
          />
          <Select
            size="small"
            value={query.status}
            onChange={(event) => dispatch(setStatus(event.target.value as typeof query.status))}
            displayEmpty
            sx={{ minWidth: 180 }}
          >
            <MenuItem value="">All Statuses</MenuItem>
            {['DRAFT', 'ACTIVE', 'PUBLISHED', 'INACTIVE', 'ARCHIVED'].map((status) => (
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
        {isLoading ? (
          <Typography color="text.secondary">Loading runtime requests...</Typography>
        ) : paged.rows.length === 0 ? (
          <EmptyState
            title="No runtime requests"
            description="Create generation requests from backend or proceed to preview/generation when requests are available."
          />
        ) : (
          <DataTable
            rows={paged.rows}
            columns={[
              {
                key: 'request',
                header: 'Request ID',
                render: (row) => normalizeRequestId(row.request_id) || '-',
              },
              {
                key: 'ref',
                header: 'Correlation ID',
                render: (row) => row.correlation_id ?? row.business_reference,
              },
              { key: 'source', header: 'Source', render: (row) => row.request_source },
              {
                key: 'status',
                header: 'Generation Status',
                render: (row) => (
                  <Chip
                    label={row.status}
                    size="small"
                    color={row.status === 'PUBLISHED' ? 'success' : row.status === 'ACTIVE' ? 'warning' : 'default'}
                    icon={row.status === 'PUBLISHED' ? <CheckCircleOutlineOutlinedIcon /> : <HourglassBottomOutlinedIcon />}
                  />
                ),
              },
              {
                key: 'progress',
                header: 'Progress Indicator',
                render: (row) => {
                  const value = row.status === 'PUBLISHED' ? 100 : row.status === 'ACTIVE' ? 65 : row.status === 'DRAFT' ? 25 : 0;
                  return <Typography>{value}%</Typography>;
                },
              },
              {
                key: 'actions',
                header: 'Actions',
                render: (row) => {
                  const requestId = normalizeRequestId(row.request_id);
                  const correlationId = (row.correlation_id ?? row.business_reference ?? '').trim();

                  return (
                    <Stack direction="row" spacing={1}>
                      <Button
                        size="small"
                        startIcon={<VisibilityOutlinedIcon fontSize="small" />}
                        disabled={!requestId}
                        onClick={() => {
                          if (!requestId) {
                            return;
                          }
                          dispatch(setSelectedRequestId(requestId));
                          dispatch(setSelectedCorrelationId(correlationId));
                          navigate(RUNTIME_ROUTES.status(requestId));
                        }}
                      >
                        Status
                      </Button>
                      <Button
                        size="small"
                        onClick={() => {
                          dispatch(setSelectedRequestId(requestId));
                          dispatch(setSelectedCorrelationId(correlationId));
                          navigate(RUNTIME_ROUTES.DOWNLOAD_CENTER);
                        }}
                      >
                        Download Center
                      </Button>
                    </Stack>
                  );
                },
              },
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
