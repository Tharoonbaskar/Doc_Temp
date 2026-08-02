import AddOutlinedIcon from '@mui/icons-material/AddOutlined';
import DeleteOutlineOutlinedIcon from '@mui/icons-material/DeleteOutlineOutlined';
import PlayArrowOutlinedIcon from '@mui/icons-material/PlayArrowOutlined';
import {
  Alert,
  Box,
  Button,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useMemo, useState } from 'react';

import { PageHeader } from '../components/common/PageHeader';
import { useConnectors } from '../features/connectors/hooks/useConnectors';
import { useDocuments } from '../features/documents/hooks/useDocuments';
import { useRuntimeGenerationRequests, useRuntimePreview } from '../features/runtime/hooks/useRuntime';
import { useTemplates } from '../features/templates/hooks/useTemplates';
import type { TemplateItem } from '../features/templates/types';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';
import { setSelectedCorrelationId, setSelectedRequestId } from '../store/slices/runtimeSlice';
import { getApiErrorMessage } from '../utils/apiErrorMessage';

type DataInputMode = 'MANUAL_INPUT' | 'CONNECTOR';

type InputFieldRow = {
  id: string;
  key: string;
  value: string;
};

const buildUuid = (): string => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }

  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (char) => {
    const randomValue = Math.floor(Math.random() * 16);
    const value = char === 'x' ? randomValue : (randomValue & 0x3) | 0x8;
    return value.toString(16);
  });
};

const pretty = (value: unknown): string => {
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return '{}';
  }
};

const DEFAULT_INPUT_ROWS: InputFieldRow[] = [
  { id: 'f-1', key: 'applicant_name', value: 'Rajesh Kumar' },
  { id: 'f-2', key: 'loan_amount', value: '5000000' },
  { id: 'f-3', key: 'interest_rate', value: '8.5' },
  { id: 'f-4', key: 'loan_tenure', value: '240' },
  { id: 'f-5', key: 'sanction_date', value: '2026-07-14' },
  { id: 'f-6', key: 'loan_reference_number', value: 'HL-2026-001' },
  { id: 'f-7', key: 'branch_name', value: 'Mumbai Central Branch' },
];

const createInputRows = (source: Record<string, unknown>): InputFieldRow[] => {
  const entries = Object.entries(source);
  if (entries.length === 0) {
    return DEFAULT_INPUT_ROWS;
  }

  return entries.map(([key, value], index) => ({
    id: `f-${index + 1}`,
    key,
    value: typeof value === 'string' ? value : JSON.stringify(value),
  }));
};

const normalizeFieldValue = (rawValue: string): unknown => {
  const trimmed = rawValue.trim();
  if (!trimmed) {
    return '';
  }

  if (trimmed.toLowerCase() === 'true') {
    return true;
  }

  if (trimmed.toLowerCase() === 'false') {
    return false;
  }

  if (/^-?\d+(\.\d+)?$/.test(trimmed)) {
    return Number(trimmed);
  }

  if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
    try {
      return JSON.parse(trimmed);
    } catch {
      return rawValue;
    }
  }

  return rawValue;
};

export function DocumentPreviewPage() {
  const dispatch = useAppDispatch();
  const mutation = useRuntimePreview();
  const connectorsQuery = useConnectors();
  const documentsQuery = useDocuments();
  const templatesQuery = useTemplates();
  const generationRequestsQuery = useRuntimeGenerationRequests();

  const connectors = useMemo(() => connectorsQuery.data ?? [], [connectorsQuery.data]);
  const documents = useMemo(() => documentsQuery.data ?? [], [documentsQuery.data]);
  const templates = useMemo(() => templatesQuery.data ?? [], [templatesQuery.data]);
  const generationRequests = useMemo(() => generationRequestsQuery.data ?? [], [generationRequestsQuery.data]);

  const [selectedDocumentId, setSelectedDocumentId] = useState('');
  const [dataInputMode, setDataInputMode] = useState<DataInputMode>('MANUAL_INPUT');
  const [inputRowsByDocument, setInputRowsByDocument] = useState<Record<string, InputFieldRow[]>>({});
  const [connectorCode, setConnectorCode] = useState('');
  const [connectorPayloadText, setConnectorPayloadText] = useState('{\n  "loan_id": "HL-2026-001"\n}');
  const [requestIdByDocument, setRequestIdByDocument] = useState<Record<string, string>>({});

  const selectedDocument = useMemo(
    () => documents.find((documentItem) => documentItem.id === selectedDocumentId),
    [documents, selectedDocumentId],
  );

  const selectedTemplate = useMemo(() => {
    if (!selectedDocumentId) {
      return undefined;
    }

    const candidates = templates.filter(
      (templateItem: TemplateItem) =>
        templateItem.document?.id === selectedDocumentId || templateItem.document_id === selectedDocumentId,
    );

    if (candidates.length === 0) {
      return undefined;
    }

    return candidates.find((templateItem: TemplateItem) => templateItem.is_default) ?? candidates[0];
  }, [selectedDocumentId, templates]);

  const templateCode = selectedTemplate?.code ?? '';

  const selectedGenerationRequest = useMemo(() => {
    if (!selectedDocumentId) {
      return undefined;
    }

    const matching = generationRequests
      .filter((request) => request.document?.id === selectedDocumentId)
      .sort((a, b) => Date.parse(b.requested_at || '') - Date.parse(a.requested_at || ''));

    return matching[0];
  }, [generationRequests, selectedDocumentId]);

  const defaultInputRows = useMemo(() => {
    if (!selectedGenerationRequest) {
      return DEFAULT_INPUT_ROWS;
    }

    const payload = selectedGenerationRequest.input_payload;
    if (payload && typeof payload === 'object' && !Array.isArray(payload)) {
      return createInputRows(payload as Record<string, unknown>);
    }

    return DEFAULT_INPUT_ROWS;
  }, [selectedGenerationRequest]);

  const inputRows = useMemo(() => {
    if (!selectedDocumentId) {
      return defaultInputRows;
    }
    return inputRowsByDocument[selectedDocumentId] ?? defaultInputRows;
  }, [defaultInputRows, inputRowsByDocument, selectedDocumentId]);

  const generationRequestId = selectedGenerationRequest?.id ?? '';
  const requestId =
    selectedGenerationRequest?.request_id ?? (selectedDocumentId ? requestIdByDocument[selectedDocumentId] ?? '' : '');
  const correlationId =
    selectedGenerationRequest?.correlation_id ?? selectedGenerationRequest?.business_reference ?? '';

  const html = mutation.data?.html ?? '';
  const history = mutation.data?.execution_history ?? [];

  const hasInputError = useMemo(() => !selectedDocumentId, [selectedDocumentId]);
  const hasConnectorSelectionError = useMemo(
    () => dataInputMode === 'CONNECTOR' && !connectorCode.trim(),
    [connectorCode, dataInputMode],
  );
  const hasTemplateMappingError = useMemo(
    () => Boolean(selectedDocumentId) && !generationRequestId && !selectedTemplate,
    [generationRequestId, selectedDocumentId, selectedTemplate],
  );
  const previewErrorMessage = useMemo(
    () => (mutation.error ? getApiErrorMessage(mutation.error, 'Failed to preview document.') : ''),
    [mutation.error],
  );

  const documentAlertSeverity = useMemo(() => {
    if (!selectedDocumentId) {
      return 'warning' as const;
    }
    if (!generationRequestId && !selectedTemplate) {
      return 'error' as const;
    }
    if (!generationRequestId) {
      return 'info' as const;
    }
    return 'success' as const;
  }, [generationRequestId, selectedDocumentId, selectedTemplate]);

  const documentHelperText = useMemo(() => {
    if (!selectedDocumentId) {
      return 'Select a document to continue.';
    }
    if (!generationRequestId && !selectedTemplate) {
      return 'No template mapped for this document. Map a template before preview.';
    }
    if (!generationRequestId) {
      return 'No runtime generation request found for this document. A request will be auto-created when you preview.';
    }
    return 'Document selected successfully.';
  }, [generationRequestId, selectedDocumentId, selectedTemplate]);

  const manualRuntimePayload = useMemo(() => {
    const payload: Record<string, unknown> = {};
    for (const row of inputRows) {
      const key = row.key.trim();
      if (!key) {
        continue;
      }
      payload[key] = normalizeFieldValue(row.value);
    }
    return payload;
  }, [inputRows]);

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Document Preview"
        subtitle="Generate runtime HTML preview and inspect execution history before final generation."
      />

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack spacing={2}>
          <FormControl fullWidth>
            <InputLabel id="preview-document-label">Select Document</InputLabel>
            <Select
              labelId="preview-document-label"
              label="Select Document"
              value={selectedDocumentId}
              renderValue={(selectedValue) => {
                const selectedText = String(selectedValue || '');
                if (!selectedText) {
                  return <Typography sx={{ color: 'text.secondary', fontStyle: 'italic' }}>Select Document</Typography>;
                }
                return documents.find((documentItem) => documentItem.id === selectedText)?.name ?? selectedText;
              }}
              onChange={(event) => {
                const nextDocumentId = event.target.value;
                setSelectedDocumentId(nextDocumentId);

                if (!nextDocumentId) {
                  return;
                }

                setRequestIdByDocument((current) => {
                  if (current[nextDocumentId]) {
                    return current;
                  }
                  return {
                    ...current,
                    [nextDocumentId]: buildUuid(),
                  };
                });
              }}
            >
              {documents.map((documentItem) => (
                <MenuItem key={documentItem.id} value={documentItem.id}>
                  {documentItem.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Alert severity={documentAlertSeverity}>{documentHelperText}</Alert>

          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <TextField
              label="Document Name"
              value={selectedDocument?.name ?? ''}
              fullWidth
              slotProps={{
                input: {
                  readOnly: true,
                },
              }}
            />
            <TextField
              label="Document UUID"
              value={selectedDocument?.id ?? ''}
              fullWidth
              slotProps={{
                input: {
                  readOnly: true,
                },
              }}
            />
          </Stack>

          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <TextField
              label="Template Name"
              value={selectedTemplate?.name ?? ''}
              helperText={selectedTemplate ? 'Mapped from selected document.' : 'No template mapped for selected document.'}
              fullWidth
              slotProps={{
                input: {
                  readOnly: true,
                },
              }}
            />
            <TextField
              label="Template UUID"
              value={selectedTemplate?.id ?? ''}
              fullWidth
              slotProps={{
                input: {
                  readOnly: true,
                },
              }}
            />
          </Stack>

          <TextField
            label="Request ID"
            value={requestId}
            helperText={
              selectedGenerationRequest?.request_id
                ? 'Runtime request identifier (mapped from generation request)'
                : 'Auto-generated UUID for request tracking.'
            }
            fullWidth
            slotProps={{
              input: {
                readOnly: true,
              },
            }}
          />

          <TextField
            label="Correlation ID"
            value={correlationId}
            fullWidth
            slotProps={{
              input: {
                readOnly: true,
              },
            }}
          />

          <FormControl fullWidth>
            <InputLabel id="preview-data-source-label">Data Source Option</InputLabel>
            <Select
              labelId="preview-data-source-label"
              label="Data Source Option"
              value={dataInputMode}
              onChange={(event) => setDataInputMode(event.target.value as DataInputMode)}
            >
              <MenuItem value="MANUAL_INPUT">Manual Input</MenuItem>
              <MenuItem value="CONNECTOR">Connector</MenuItem>
            </Select>
          </FormControl>

          {dataInputMode === 'MANUAL_INPUT' ? (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Stack spacing={1.5}>
                <Typography variant="subtitle2">Input Data Fields</Typography>
                {inputRows.map((row, index) => (
                  <Stack key={row.id} direction={{ xs: 'column', md: 'row' }} spacing={1} alignItems={{ md: 'center' }}>
                    <TextField
                      label={`Field ${index + 1} Name`}
                      value={row.key}
                      onChange={(event) => {
                        if (!selectedDocumentId) {
                          return;
                        }

                        setInputRowsByDocument((current) => {
                          const baseRows = current[selectedDocumentId] ?? defaultInputRows;
                          return {
                            ...current,
                            [selectedDocumentId]: baseRows.map((item) =>
                              item.id === row.id ? { ...item, key: event.target.value } : item,
                            ),
                          };
                        });
                      }}
                      fullWidth
                    />
                    <TextField
                      label="Value"
                      value={row.value}
                      onChange={(event) => {
                        if (!selectedDocumentId) {
                          return;
                        }

                        setInputRowsByDocument((current) => {
                          const baseRows = current[selectedDocumentId] ?? defaultInputRows;
                          return {
                            ...current,
                            [selectedDocumentId]: baseRows.map((item) =>
                              item.id === row.id ? { ...item, value: event.target.value } : item,
                            ),
                          };
                        });
                      }}
                      fullWidth
                    />
                    <IconButton
                      aria-label="Delete field"
                      onClick={() => {
                        if (!selectedDocumentId) {
                          return;
                        }

                        setInputRowsByDocument((current) => {
                          const baseRows = current[selectedDocumentId] ?? defaultInputRows;
                          return {
                            ...current,
                            [selectedDocumentId]: baseRows.filter((item) => item.id !== row.id),
                          };
                        });
                      }}
                    >
                      <DeleteOutlineOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Stack>
                ))}

                <Stack direction="row" spacing={1}>
                  <Button
                    startIcon={<AddOutlinedIcon />}
                    onClick={() => {
                      if (!selectedDocumentId) {
                        return;
                      }

                      setInputRowsByDocument((current) => {
                        const baseRows = current[selectedDocumentId] ?? defaultInputRows;
                        return {
                          ...current,
                          [selectedDocumentId]: [
                            ...baseRows,
                            {
                              id: `f-${Date.now()}`,
                              key: '',
                              value: '',
                            },
                          ],
                        };
                      });
                    }}
                  >
                    Add Input Field
                  </Button>
                </Stack>
              </Stack>
            </Paper>
          ) : (
            <Paper variant="outlined" sx={{ p: 2 }}>
              <Stack spacing={2}>
                <Typography variant="subtitle2">Connector Input</Typography>
                <FormControl fullWidth error={hasConnectorSelectionError}>
                  <InputLabel id="preview-connector-label">Connector Name</InputLabel>
                  <Select
                    labelId="preview-connector-label"
                    label="Connector Name"
                    value={connectorCode}
                    onChange={(event) => setConnectorCode(event.target.value)}
                  >
                    {connectors.length === 0 ? (
                      <MenuItem value="" disabled>
                        No connectors available
                      </MenuItem>
                    ) : (
                      connectors.map((connectorItem) => (
                        <MenuItem key={connectorItem.id} value={connectorItem.code}>
                          {connectorItem.name}
                        </MenuItem>
                      ))
                    )}
                  </Select>
                </FormControl>
                <TextField
                  label="Connector Code"
                  value={connectorCode}
                  helperText={
                    hasConnectorSelectionError
                      ? 'Select connector name to continue.'
                      : 'Auto-populated from selected connector.'
                  }
                  fullWidth
                  slotProps={{
                    input: {
                      readOnly: true,
                    },
                  }}
                />
                <TextField
                  label="Connector Payload (JSON)"
                  value={connectorPayloadText}
                  onChange={(event) => setConnectorPayloadText(event.target.value)}
                  multiline
                  minRows={6}
                  fullWidth
                />
              </Stack>
            </Paper>
          )}

          <Stack direction="row" spacing={1}>
            <Button
              variant="contained"
              startIcon={<PlayArrowOutlinedIcon />}
              disabled={mutation.isPending || hasInputError || hasConnectorSelectionError || hasTemplateMappingError}
              onClick={async () => {
                try {
                  const payload: {
                    generation_request_id?: string;
                    document_id?: string;
                    runtime_payload: Record<string, unknown>;
                    template_code?: string;
                    correlation_id?: string;
                    connector_code?: string;
                    connector_payload?: Record<string, unknown>;
                  } = {
                    runtime_payload: manualRuntimePayload,
                  };

                  if (correlationId) {
                    payload.correlation_id = correlationId;
                  }

                  if (generationRequestId) {
                    payload.generation_request_id = generationRequestId;
                  } else {
                    payload.document_id = selectedDocumentId;
                  }

                  if (templateCode) {
                    payload.template_code = templateCode;
                  }

                  if (dataInputMode === 'CONNECTOR') {
                    payload.connector_code = connectorCode || undefined;
                    payload.connector_payload = JSON.parse(connectorPayloadText || '{}') as Record<string, unknown>;
                  }

                  const response = await mutation.mutateAsync(payload);
                  const nextRequestId = response.request_id ?? '';

                  setRequestIdByDocument((current) =>
                    selectedDocumentId && nextRequestId
                      ? {
                          ...current,
                          [selectedDocumentId]: nextRequestId,
                        }
                      : current,
                  );
                  dispatch(setSelectedRequestId(nextRequestId));
                  dispatch(
                    setSelectedCorrelationId(response.correlation_id ?? response.business_reference ?? correlationId),
                  );
                  dispatch(
                    enqueueNotification({
                      severity: 'success',
                      message: 'Preview generated successfully.',
                    }),
                  );
                } catch (error) {
                  dispatch(
                    enqueueNotification({
                      severity: 'error',
                      message: getApiErrorMessage(error, 'Preview failed. Verify selected document and input data.'),
                    }),
                  );
                }
              }}
            >
              {mutation.isPending ? 'Generating Preview...' : 'Generate Preview'}
            </Button>
          </Stack>
        </Stack>
      </Paper>

      {mutation.error ? <Alert severity="error">{previewErrorMessage}</Alert> : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle1" sx={{ mb: 1 }}>
          PDF Preview (HTML)
        </Typography>
        {html ? (
          <Box
            sx={{
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 1,
              p: 2,
              maxHeight: 520,
              overflow: 'auto',
              bgcolor: 'background.paper',
            }}
            dangerouslySetInnerHTML={{ __html: html }}
          />
        ) : (
          <Typography color="text.secondary">No preview available yet.</Typography>
        )}
      </Paper>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="subtitle1" sx={{ mb: 1 }}>
          History
        </Typography>
        {history.length === 0 ? (
          <Typography color="text.secondary">No runtime history captured yet.</Typography>
        ) : (
          <Stack spacing={1}>
            {history.map((item, index) => (
              <Box key={`${item.stage_name ?? item.stage ?? 'STAGE'}-${index}`} sx={{ border: '1px solid', borderColor: 'divider', p: 1.5, borderRadius: 1 }}>
                <Typography variant="body2">
                  <strong>{item.stage_name ?? item.stage ?? 'STAGE'}</strong> - {item.stage_status ?? item.status ?? 'UNKNOWN'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  Duration: {item.duration_ms ?? 0} ms
                </Typography>
                <Typography variant="body2" sx={{ mt: 1, whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                  {pretty(item.details_json ?? item.details ?? {})}
                </Typography>
              </Box>
            ))}
          </Stack>
        )}
      </Paper>
    </Stack>
  );
}
