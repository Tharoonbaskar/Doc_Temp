import CloudDownloadOutlinedIcon from '@mui/icons-material/CloudDownloadOutlined';
import SearchOutlinedIcon from '@mui/icons-material/SearchOutlined';
import {
  Alert,
  Button,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';

import { PageHeader } from '../components/common/PageHeader';
import { useRuntimeDownload, useRuntimeHistory } from '../features/runtime/hooks/useRuntime';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';
import { setSelectedCorrelationId } from '../store/slices/runtimeSlice';

export function DownloadCenterPage() {
  const dispatch = useAppDispatch();
  const selectedRequestId = useAppSelector((state) => state.runtime.selectedRequestId);
  const selectedCorrelationId = useAppSelector(
    (state) => state.runtime.selectedCorrelationId || state.runtime.selectedBusinessReference,
  );

  const [requestId, setRequestId] = useState(selectedRequestId ?? '');
  const [correlationId, setCorrelationId] = useState(selectedCorrelationId ?? '');

  const normalizedRequestId = requestId.trim();
  const normalizedCorrelationId = correlationId.trim();

  const historyQuery = useRuntimeHistory(normalizedCorrelationId);
  const downloadMutation = useRuntimeDownload();

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Download Center"
        subtitle="Retrieve generated artifacts and browse generation history by correlation ID."
      />

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <TextField
            label="Request ID"
            value={requestId}
            onChange={(event) => setRequestId(event.target.value)}
            fullWidth
          />
          <Button
            variant="contained"
            startIcon={<CloudDownloadOutlinedIcon />}
            disabled={!normalizedRequestId || downloadMutation.isPending}
            onClick={async () => {
              try {
                const result = await downloadMutation.mutateAsync(normalizedRequestId);
                const url = result.download_url ?? result.file_url;
                if (url) {
                  window.open(url, '_blank', 'noopener,noreferrer');
                  dispatch(enqueueNotification({ severity: 'success', message: 'Download initiated.' }));
                  return;
                }

                dispatch(
                  enqueueNotification({
                    severity: 'warning',
                    message: `No downloadable file is available for request status ${result.status}.`,
                  }),
                );
              } catch {
                dispatch(enqueueNotification({ severity: 'error', message: 'Download failed. Check request ID.' }));
              }
            }}
          >
            Download
          </Button>
        </Stack>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <TextField
            label="Correlation ID"
            value={correlationId}
            onChange={(event) => setCorrelationId(event.target.value)}
            fullWidth
          />
          <Button
            variant="outlined"
            startIcon={<SearchOutlinedIcon />}
            disabled={!normalizedCorrelationId}
            onClick={() => {
              dispatch(setSelectedCorrelationId(normalizedCorrelationId));
              historyQuery.refetch();
            }}
          >
            Load History
          </Button>
        </Stack>
      </Paper>

      {historyQuery.error ? <Alert severity="error">Failed to load generation history.</Alert> : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle1" sx={{ mb: 1 }}>
          History
        </Typography>
        {historyQuery.isLoading ? (
          <Typography color="text.secondary">Loading history...</Typography>
        ) : historyQuery.data?.history?.length ? (
          <Stack spacing={1}>
            {historyQuery.data.history.map((item) => {
              const canDownload = Boolean(item.download_url || item.generated_document?.file_name);

              return (
                <Stack
                  key={item.request_id}
                  direction={{ xs: 'column', md: 'row' }}
                  spacing={1}
                  justifyContent="space-between"
                  sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 1, p: 1.5 }}
                >
                  <Stack spacing={0.5}>
                    <Typography variant="body2"><strong>Request:</strong> {item.request_id}</Typography>
                    <Typography variant="body2">
                      <strong>Correlation ID:</strong> {item.correlation_id ?? item.business_reference ?? '-'}
                    </Typography>
                    <Typography variant="body2"><strong>Status:</strong> {item.status}</Typography>
                    <Typography variant="body2"><strong>Requested:</strong> {item.requested_at ?? '-'}</Typography>
                    <Typography variant="body2"><strong>File:</strong> {item.generated_document?.file_name ?? '-'}</Typography>
                    {!canDownload ? (
                      <Typography variant="caption" color="text.secondary">
                        File is not available yet for this request. Generate/publish first.
                      </Typography>
                    ) : null}
                  </Stack>
                  <Stack direction="row" spacing={1}>
                    <Button
                      size="small"
                      disabled={!canDownload || downloadMutation.isPending}
                      onClick={async () => {
                        if (!canDownload) {
                          dispatch(
                            enqueueNotification({
                              severity: 'warning',
                              message: 'This request has no generated file yet.',
                            }),
                          );
                          return;
                        }

                        try {
                          const result = await downloadMutation.mutateAsync(item.request_id);
                          const url = result.download_url ?? result.file_url;
                          if (url) {
                            window.open(url, '_blank', 'noopener,noreferrer');
                            dispatch(enqueueNotification({ severity: 'success', message: 'Download initiated.' }));
                            return;
                          }

                          dispatch(
                            enqueueNotification({
                              severity: 'warning',
                              message: `No downloadable file is available for request status ${result.status}.`,
                            }),
                          );
                        } catch {
                          dispatch(enqueueNotification({ severity: 'error', message: 'Unable to download this item.' }));
                        }
                      }}
                    >
                      Download
                    </Button>
                  </Stack>
                </Stack>
              );
            })}
          </Stack>
        ) : (
          <Typography color="text.secondary">No history found for the current correlation ID.</Typography>
        )}
      </Paper>
    </Stack>
  );
}
