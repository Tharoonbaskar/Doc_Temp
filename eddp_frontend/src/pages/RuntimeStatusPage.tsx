import DownloadOutlinedIcon from '@mui/icons-material/DownloadOutlined';
import RefreshOutlinedIcon from '@mui/icons-material/RefreshOutlined';
import {
  Alert,
  Box,
  Button,
  Chip,
  LinearProgress,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { PageHeader } from '../components/common/PageHeader';
import { RUNTIME_ROUTES } from '../constants/appConstants';
import { useRuntimeDownload, useRuntimeStatus } from '../features/runtime/hooks/useRuntime';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';

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

export function RuntimeStatusPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { requestId: routeRequestId } = useParams();
  const selectedRequestId = useAppSelector((state) => state.runtime.selectedRequestId);
  const activeRequestId = normalizeRequestId(routeRequestId) || normalizeRequestId(selectedRequestId);
  const hasInvalidRouteRequestId = Boolean(routeRequestId) && !normalizeRequestId(routeRequestId);

  const [manualRequestId, setManualRequestId] = useState(activeRequestId);
  const normalizedManualRequestId = normalizeRequestId(manualRequestId);

  const query = useRuntimeStatus(normalizedManualRequestId);
  const downloadMutation = useRuntimeDownload();

  const progress = useMemo(() => {
    const stages = query.data?.execution_history ?? [];
    if (stages.length === 0) {
      return query.data?.status === 'PUBLISHED' ? 100 : query.data?.status === 'ACTIVE' ? 50 : 0;
    }
    const done = stages.filter((item) => (item.stage_status ?? item.status ?? '').toUpperCase() === 'SUCCESS').length;
    return Math.round((done / stages.length) * 100);
  }, [query.data?.execution_history, query.data?.status]);

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Generation Status"
        subtitle="Track progress indicators, execution stages, and download availability."
        actions={
          <Button variant="outlined" onClick={() => navigate(RUNTIME_ROUTES.DOWNLOAD_CENTER)} startIcon={<DownloadOutlinedIcon />}>
            Download Center
          </Button>
        }
      />

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <TextField
            label="Request ID"
            value={manualRequestId}
            onChange={(event) => setManualRequestId(event.target.value)}
            fullWidth
          />
          <Button
            variant="contained"
            startIcon={<RefreshOutlinedIcon />}
            onClick={() => {
              if (normalizedManualRequestId) {
                query.refetch();
              }
            }}
            disabled={!normalizedManualRequestId || query.isFetching}
          >
            Refresh
          </Button>
        </Stack>
      </Paper>

      {hasInvalidRouteRequestId ? (
        <Alert severity="warning">Invalid request ID in URL. Enter a valid Request ID to load status.</Alert>
      ) : null}

      {query.error ? <Alert severity="error">Failed to load generation status.</Alert> : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle1" sx={{ mb: 1 }}>
          Progress Indicator
        </Typography>
        <LinearProgress variant="determinate" value={progress} sx={{ height: 8, borderRadius: 999 }} />
        <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            {query.isLoading ? 'Loading...' : `${progress}% complete`}
          </Typography>
          {query.data?.status ? <Chip label={query.data.status} size="small" /> : null}
        </Stack>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle1" sx={{ mb: 1 }}>
          Generation Status Details
        </Typography>
        {query.data ? (
          <Stack spacing={1}>
            <Typography variant="body2"><strong>Request ID:</strong> {query.data.request_id}</Typography>
            <Typography variant="body2">
              <strong>Correlation ID:</strong> {query.data.correlation_id ?? query.data.business_reference}
            </Typography>
            <Typography variant="body2"><strong>Status:</strong> {query.data.status}</Typography>
            <Typography variant="body2"><strong>Requested At:</strong> {query.data.requested_at ?? '-'}</Typography>
            <Typography variant="body2"><strong>Completed At:</strong> {query.data.completed_at ?? '-'}</Typography>
            <Typography variant="body2"><strong>Processing Time:</strong> {query.data.processing_time_ms ?? 0} ms</Typography>
            {query.data.generated_document?.file_name ? (
              <Typography variant="body2"><strong>Output:</strong> {query.data.generated_document.file_name}</Typography>
            ) : null}
            {query.data.download_url ? (
              <Button
                size="small"
                onClick={async () => {
                  try {
                    const requestId = normalizeRequestId(query.data?.request_id);
                    if (!requestId) {
                      dispatch(enqueueNotification({ severity: 'warning', message: 'No valid request ID available for download.' }));
                      return;
                    }

                    const result = await downloadMutation.mutateAsync(requestId);
                    const url = result.download_url ?? result.file_url;
                    if (url) {
                      window.open(url, '_blank', 'noopener,noreferrer');
                    }
                    dispatch(enqueueNotification({ severity: 'success', message: 'Download started.' }));
                  } catch {
                    dispatch(enqueueNotification({ severity: 'error', message: 'Unable to start download.' }));
                  }
                }}
              >
                Download
              </Button>
            ) : null}
          </Stack>
        ) : (
          <Typography color="text.secondary">Provide a request ID to view status.</Typography>
        )}
      </Paper>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle1" sx={{ mb: 1 }}>
          History
        </Typography>
        {query.data?.execution_history?.length ? (
          <Stack spacing={1}>
            {query.data.execution_history.map((stage, index) => {
              const name = stage.stage_name ?? stage.stage ?? `STAGE_${index + 1}`;
              const status = stage.stage_status ?? stage.status ?? 'UNKNOWN';
              return (
                <Box key={`${name}-${index}`} sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 1, p: 1.5 }}>
                  <Typography variant="body2"><strong>{name}</strong> - {status}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Started: {stage.started_at ?? '-'} | Completed: {stage.completed_at ?? '-'} | Duration: {stage.duration_ms ?? 0} ms
                  </Typography>
                </Box>
              );
            })}
          </Stack>
        ) : (
          <Typography color="text.secondary">No execution history for this request yet.</Typography>
        )}
      </Paper>
    </Stack>
  );
}
