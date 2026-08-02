import DownloadOutlinedIcon from '@mui/icons-material/DownloadOutlined';
import PlayArrowOutlinedIcon from '@mui/icons-material/PlayArrowOutlined';
import {
  Alert,
  Button,
  LinearProgress,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '../components/common/PageHeader';
import { RUNTIME_ROUTES } from '../constants/appConstants';
import { useRuntimeGenerate, useRuntimeGenerationRequests } from '../features/runtime/hooks/useRuntime';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';
import { setSelectedCorrelationId, setSelectedRequestId } from '../store/slices/runtimeSlice';
import { getApiErrorMessage } from '../utils/apiErrorMessage';

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

const normalizeLookupValue = (value: string | null | undefined): string =>
  (value ?? '').trim().toLowerCase();

const isUuid = (value: string): boolean =>
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(value);

export function DocumentGenerationPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const selectedRequestId = useAppSelector((state) => state.runtime.selectedRequestId);
  const selectedCorrelationId = useAppSelector(
    (state) => state.runtime.selectedCorrelationId || state.runtime.selectedBusinessReference,
  );
  const mutation = useRuntimeGenerate();
  const generationRequestsQuery = useRuntimeGenerationRequests();

  const [generationRequestId, setGenerationRequestId] = useState(selectedRequestId ?? '');
  const [outputFormat, setOutputFormat] = useState<'PDF' | 'DOCX'>('PDF');
  const [fileName, setFileName] = useState('');
  const [runtimePayloadText, setRuntimePayloadText] = useState('{\n  "customer": "Acme",\n  "amount": 1200\n}');

  const normalizedGenerationRequestId = normalizeRequestId(generationRequestId);

  const generationRequestMatches = useMemo(() => {
    const lookupValue = normalizedGenerationRequestId.toLowerCase();
    if (!lookupValue) {
      return [];
    }

    const requests = generationRequestsQuery.data ?? [];
    const matched = requests.filter((requestItem) => {
      const requestId = normalizeRequestId(requestItem.request_id).toLowerCase();
      const generationRequestIdValue = normalizeRequestId(requestItem.id).toLowerCase();
      const correlationValue = normalizeLookupValue(
        requestItem.correlation_id ?? requestItem.business_reference,
      );

      return (
        requestId === lookupValue ||
        generationRequestIdValue === lookupValue ||
        correlationValue === lookupValue
      );
    });

    return matched
      .slice()
      .sort(
        (left, right) =>
          Date.parse(right.requested_at || '') - Date.parse(left.requested_at || ''),
      );
  }, [generationRequestsQuery.data, normalizedGenerationRequestId]);

  const resolvedGenerationRequestId = useMemo(() => {
    if (generationRequestMatches.length > 0) {
      return normalizeRequestId(generationRequestMatches[0].id);
    }
    return normalizedGenerationRequestId;
  }, [generationRequestMatches, normalizedGenerationRequestId]);

  const hasResolvableGenerationRequest =
    Boolean(resolvedGenerationRequestId) &&
    (generationRequestMatches.length > 0 || isUuid(resolvedGenerationRequestId));

  const generationRequestHelperText = useMemo(() => {
    if (!normalizedGenerationRequestId) {
      return 'Enter Generation Request ID, Request ID, or Correlation ID.';
    }

    if (generationRequestMatches.length === 0) {
      return isUuid(normalizedGenerationRequestId)
        ? 'Using entered value as generation_request_id.'
        : 'No matching request found. Enter a valid request UUID or known correlation ID.';
    }

    const topMatch = generationRequestMatches[0];
    const inputValue = normalizedGenerationRequestId.toLowerCase();
    const generationId = normalizeRequestId(topMatch.id);
    const requestId = normalizeRequestId(topMatch.request_id);

    if (generationId.toLowerCase() === inputValue) {
      return 'Resolved as Generation Request ID.';
    }

    if (requestId.toLowerCase() === inputValue) {
      return `Resolved Request ID to generation request ${generationId}.`;
    }

    return `Resolved Correlation ID to request ${requestId}.`;
  }, [generationRequestMatches, normalizedGenerationRequestId]);

  const progress = useMemo(() => {
    if (mutation.isPending) {
      return 65;
    }
    if (mutation.data?.status === 'PUBLISHED') {
      return 100;
    }
    return 0;
  }, [mutation.data?.status, mutation.isPending]);

  const requestId = normalizeRequestId(mutation.data?.request_id) || normalizeRequestId(selectedRequestId);

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Document Generation"
        subtitle="Generate PDF or DOCX with runtime orchestration and progress tracking."
        actions={
          <Button
            variant="outlined"
            startIcon={<DownloadOutlinedIcon />}
            onClick={() => navigate(RUNTIME_ROUTES.DOWNLOAD_CENTER)}
          >
            Open Download Center
          </Button>
        }
      />

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack spacing={2}>
          <TextField
            label="Generation Request ID"
            value={generationRequestId}
            onChange={(event) => setGenerationRequestId(event.target.value)}
            helperText={generationRequestHelperText}
            error={Boolean(normalizedGenerationRequestId) && !hasResolvableGenerationRequest}
            fullWidth
          />
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <Select
              size="small"
              value={outputFormat}
              onChange={(event) => setOutputFormat(event.target.value as 'PDF' | 'DOCX')}
              sx={{ minWidth: 180 }}
            >
              <MenuItem value="PDF">PDF</MenuItem>
              <MenuItem value="DOCX">DOCX</MenuItem>
            </Select>
            <TextField
              label="File Name (optional)"
              value={fileName}
              onChange={(event) => setFileName(event.target.value)}
              fullWidth
            />
          </Stack>
          <TextField
            label="Runtime Payload (JSON)"
            value={runtimePayloadText}
            onChange={(event) => setRuntimePayloadText(event.target.value)}
            multiline
            minRows={6}
            fullWidth
          />

          <Button
            variant="contained"
            startIcon={<PlayArrowOutlinedIcon />}
            disabled={mutation.isPending || !hasResolvableGenerationRequest}
            onClick={async () => {
              try {
                const runtimePayload = JSON.parse(runtimePayloadText || '{}') as Record<string, unknown>;
                const response = await mutation.mutateAsync({
                  generation_request_id: resolvedGenerationRequestId,
                  correlation_id: selectedCorrelationId || undefined,
                  runtime_payload: runtimePayload,
                  output_format: outputFormat,
                  file_name: fileName || undefined,
                });
                dispatch(setSelectedRequestId(normalizeRequestId(response.request_id)));
                dispatch(
                  setSelectedCorrelationId(
                    response.correlation_id ?? response.business_reference ?? selectedCorrelationId,
                  ),
                );
                dispatch(enqueueNotification({ severity: 'success', message: 'Document generated successfully.' }));
              } catch (error) {
                dispatch(
                  enqueueNotification({
                    severity: 'error',
                    message: getApiErrorMessage(error, 'Generation failed. Verify request and payload.'),
                  }),
                );
              }
            }}
          >
            {mutation.isPending ? 'Generating...' : 'Generate Document'}
          </Button>
        </Stack>
      </Paper>

      {mutation.error ? <Alert severity="error">Failed to generate document.</Alert> : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle1" sx={{ mb: 1 }}>
          Generation Status
        </Typography>
        <LinearProgress variant="determinate" value={progress} sx={{ height: 8, borderRadius: 999 }} />
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {mutation.isPending ? 'Running runtime orchestration...' : mutation.data?.status ?? 'Idle'}
        </Typography>

        {mutation.data?.generated_document ? (
          <Stack spacing={1} sx={{ mt: 2 }}>
            <Typography variant="body2"><strong>Request ID:</strong> {mutation.data.request_id}</Typography>
            <Typography variant="body2">
              <strong>Correlation ID:</strong> {mutation.data.correlation_id ?? mutation.data.business_reference ?? '-'}
            </Typography>
            <Typography variant="body2"><strong>File:</strong> {mutation.data.generated_document.file_name}</Typography>
            <Typography variant="body2"><strong>Type:</strong> {mutation.data.generated_document.file_type}</Typography>
            <Typography variant="body2"><strong>Size:</strong> {mutation.data.generated_document.file_size} bytes</Typography>
            {mutation.data.download_url ? (
              <Button size="small" onClick={() => window.open(mutation.data?.download_url, '_blank', 'noopener,noreferrer')}>
                Download
              </Button>
            ) : null}
          </Stack>
        ) : null}

        {requestId ? (
          <Button sx={{ mt: 2 }} onClick={() => navigate(RUNTIME_ROUTES.status(requestId))}>
            View Detailed Status
          </Button>
        ) : null}
      </Paper>
    </Stack>
  );
}
