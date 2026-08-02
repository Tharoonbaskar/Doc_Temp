import DownloadOutlinedIcon from '@mui/icons-material/DownloadOutlined';
import PictureAsPdfOutlinedIcon from '@mui/icons-material/PictureAsPdfOutlined';
import PrintOutlinedIcon from '@mui/icons-material/PrintOutlined';
import SaveOutlinedIcon from '@mui/icons-material/SaveOutlined';
import VisibilityOutlinedIcon from '@mui/icons-material/VisibilityOutlined';
import {
  Alert,
  Box,
  Button,
  FormControlLabel,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Switch,
  TextField,
  Typography,
} from '@mui/material';
import { useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { LoadingOverlay } from '../components/common/LoadingOverlay';
import { PageHeader } from '../components/common/PageHeader';
import { TEMPLATE_ROUTES } from '../constants/appConstants';
import { templatesApi } from '../features/templates/api/templatesApi';
import { useTemplatePdfGenerate, useTemplatePdfPreview, useTemplate } from '../features/templates/hooks/useTemplates';
import type { TemplatePdfRequestPayload, TemplatePdfVariableResolutionMode } from '../features/templates/types';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';
import { getApiErrorMessage } from '../utils/apiErrorMessage';

const DEFAULT_VARIABLES_JSON = JSON.stringify(
  {
    APPLICANT_NAME: 'THAROON',
    CUSTOMER_ID: 'CUS0004567',
    LOAN_AMOUNT: '25,00,000',
    INTEREST_RATE: '9.5%',
  },
  null,
  2,
);

const DEFAULT_METADATA_JSON = JSON.stringify(
  {
    Organization: 'EDDP Enterprise',
    Classification: 'CONFIDENTIAL',
  },
  null,
  2,
);

export function TemplatePdfStudioPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { id = '' } = useParams();

  const templateQuery = useTemplate(id);
  const previewMutation = useTemplatePdfPreview();
  const generateMutation = useTemplatePdfGenerate();

  const [version, setVersion] = useState('');
  const [variablesText, setVariablesText] = useState(DEFAULT_VARIABLES_JSON);
  const [metadataText, setMetadataText] = useState(DEFAULT_METADATA_JSON);

  const [pageSize, setPageSize] = useState<'A4' | 'A3' | 'LETTER' | 'LEGAL'>('A4');
  const [orientation, setOrientation] = useState<'PORTRAIT' | 'LANDSCAPE'>('PORTRAIT');
  const [marginTop, setMarginTop] = useState<number>(14);
  const [marginBottom, setMarginBottom] = useState<number>(14);
  const [marginLeft, setMarginLeft] = useState<number>(14);
  const [marginRight, setMarginRight] = useState<number>(14);
  const [resolutionDpi, setResolutionDpi] = useState<number>(150);
  const [watermark, setWatermark] = useState<string>('');
  const [includeHeaderFooter, setIncludeHeaderFooter] = useState<boolean>(true);
  const [includePageNumbers, setIncludePageNumbers] = useState<boolean>(true);
  const [variableMode, setVariableMode] = useState<TemplatePdfVariableResolutionMode>('RESOLVE_STRICT');
  const [fontEmbedding, setFontEmbedding] = useState<boolean>(true);
  const [fontFamily, setFontFamily] = useState<string>('Times New Roman');
  const [fileName, setFileName] = useState<string>('');
  const [password, setPassword] = useState<string>('');
  const [restrictPrinting, setRestrictPrinting] = useState<boolean>(false);
  const [restrictCopy, setRestrictCopy] = useState<boolean>(false);

  const previewData = previewMutation.data;
  const generateData = generateMutation.data;

  const previewSrc = useMemo(() => {
    if (!previewData?.preview_base64) {
      return '';
    }
    const mimeType = previewData.mime_type || 'application/pdf';
    return `data:${mimeType};base64,${previewData.preview_base64}`;
  }, [previewData]);

  const parseJsonObject = (value: string, label: string): Record<string, unknown> => {
    const parsed = JSON.parse(value || '{}') as unknown;
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      throw new Error(`${label} must be a JSON object.`);
    }
    return parsed as Record<string, unknown>;
  };

  const buildPayload = (previewMode: boolean): TemplatePdfRequestPayload => {
    const variables = parseJsonObject(variablesText, 'Variables');
    const metadata = parseJsonObject(metadataText, 'Metadata');

    return {
      version: version.trim() || undefined,
      variables,
      metadata,
      file_name: fileName.trim() || undefined,
      pdf_options: {
        page_size: pageSize,
        orientation,
        margin_top_mm: marginTop,
        margin_bottom_mm: marginBottom,
        margin_left_mm: marginLeft,
        margin_right_mm: marginRight,
        resolution_dpi: resolutionDpi,
        watermark: watermark.trim() || undefined,
        include_header_footer: includeHeaderFooter,
        include_page_numbers: includePageNumbers,
        variable_resolution_mode: variableMode,
        font_embedding: fontEmbedding,
        font_family: fontFamily.trim() || undefined,
        preview_unresolved: previewMode && variableMode === 'KEEP_UNRESOLVED',
        security:
          password.trim() || restrictCopy || restrictPrinting
            ? {
                password: password.trim() || undefined,
                restrict_printing: restrictPrinting,
                restrict_copy: restrictCopy,
              }
            : undefined,
      },
    };
  };

  const handlePreview = async () => {
    try {
      const payload = buildPayload(true);
      await previewMutation.mutateAsync({ templateId: id, payload });
      dispatch(enqueueNotification({ severity: 'success', message: 'PDF preview generated.' }));
    } catch (error) {
      dispatch(enqueueNotification({ severity: 'error', message: getApiErrorMessage(error, 'Preview generation failed.') }));
    }
  };

  const handleGenerate = async (saveCopyMode: boolean) => {
    try {
      const payload = buildPayload(false);
      if (saveCopyMode && !payload.file_name) {
        payload.file_name = `copy-${Date.now()}.pdf`;
      }

      const result = await generateMutation.mutateAsync({ templateId: id, payload });
      const targetUrl = result.file_url || result.download_url;
      if (targetUrl) {
        window.open(targetUrl, '_blank', 'noopener,noreferrer');
      }
      dispatch(enqueueNotification({ severity: 'success', message: 'PDF generated successfully.' }));
    } catch (error) {
      dispatch(enqueueNotification({ severity: 'error', message: getApiErrorMessage(error, 'PDF generation failed.') }));
    }
  };

  const handlePrint = () => {
    if (!previewSrc) {
      dispatch(enqueueNotification({ severity: 'warning', message: 'Generate a preview before printing.' }));
      return;
    }

    const printWindow = window.open('', '_blank', 'noopener,noreferrer');
    if (!printWindow) {
      dispatch(enqueueNotification({ severity: 'error', message: 'Unable to open print window.' }));
      return;
    }

    printWindow.document.write(
      `<iframe src="${previewSrc}" style="border:0;width:100%;height:100vh;"></iframe>`,
    );
    printWindow.document.close();
    setTimeout(() => {
      printWindow.focus();
      printWindow.print();
    }, 500);
  };

  if (templateQuery.isLoading) {
    return <LoadingOverlay open />;
  }

  if (templateQuery.error) {
    return <Alert severity="error">Failed to load template details.</Alert>;
  }

  if (!templateQuery.data) {
    return <EmptyState title="Template not found" description="Unable to open the PDF studio for this template." />;
  }

  const template = templateQuery.data;
  const isApproved = template.status === 'APPROVED';
  const selectedVersionLabel = version.trim() || `v${template.current_version ?? 1}.0`;
  let latestApprovedDownloadUrl = templatesApi.downloadPdfUrl(template.id, {
    version: version.trim() || undefined,
    variable_resolution_mode: variableMode,
    watermark: watermark.trim() || undefined,
  });

  try {
    latestApprovedDownloadUrl = templatesApi.downloadPdfUrl(template.id, {
      version: version.trim() || undefined,
      variables: parseJsonObject(variablesText, 'Variables'),
      variable_resolution_mode: variableMode,
      watermark: watermark.trim() || undefined,
    });
  } catch {
    // Fall back to URL without variables when JSON is invalid.
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        title="Enterprise PDF Generation"
        subtitle="ProseMirror-first rendering pipeline with approved-version enforcement"
        actions={
          <Button variant="outlined" onClick={() => navigate(TEMPLATE_ROUTES.view(template.id))}>
            Back To Template
          </Button>
        }
      />

      {!isApproved ? (
        <Alert severity="warning">
          This template is currently {template.status}. Only APPROVED templates can be previewed or downloaded as PDF.
        </Alert>
      ) : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>Document Information</Typography>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography variant="body2" color="text.secondary">Template Name</Typography>
            <Typography>{template.name}</Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography variant="body2" color="text.secondary">Template Code</Typography>
            <Typography>{template.code}</Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography variant="body2" color="text.secondary">Approved Version</Typography>
            <Typography>{selectedVersionLabel}</Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography variant="body2" color="text.secondary">Status</Typography>
            <Typography>{template.status}</Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography variant="body2" color="text.secondary">Generated By</Typography>
            <Typography>{previewData?.generated_by || generateData?.generated_by || '-'}</Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Typography variant="body2" color="text.secondary">Generated Date</Typography>
            <Typography>{previewData?.generated_date || generateData?.generated_date || '-'}</Typography>
          </Grid>
        </Grid>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>PDF Options</Typography>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 3 }}>
            <TextField
              label="Approved Version"
              value={version}
              onChange={(event) => setVersion(event.target.value)}
              fullWidth
              helperText="Leave blank to use latest approved"
            />
          </Grid>
          <Grid size={{ xs: 12, md: 3 }}>
            <InputLabel id="pdf-page-size-label">Page Size</InputLabel>
            <Select
              labelId="pdf-page-size-label"
              value={pageSize}
              onChange={(event) => setPageSize(event.target.value as 'A4' | 'A3' | 'LETTER' | 'LEGAL')}
              fullWidth
            >
              <MenuItem value="A4">A4</MenuItem>
              <MenuItem value="A3">A3</MenuItem>
              <MenuItem value="LETTER">Letter</MenuItem>
              <MenuItem value="LEGAL">Legal</MenuItem>
            </Select>
          </Grid>
          <Grid size={{ xs: 12, md: 3 }}>
            <InputLabel id="pdf-orientation-label">Orientation</InputLabel>
            <Select
              labelId="pdf-orientation-label"
              value={orientation}
              onChange={(event) => setOrientation(event.target.value as 'PORTRAIT' | 'LANDSCAPE')}
              fullWidth
            >
              <MenuItem value="PORTRAIT">Portrait</MenuItem>
              <MenuItem value="LANDSCAPE">Landscape</MenuItem>
            </Select>
          </Grid>
          <Grid size={{ xs: 12, md: 3 }}>
            <TextField
              label="Resolution (DPI)"
              type="number"
              value={resolutionDpi}
              onChange={(event) => setResolutionDpi(Number(event.target.value || 150))}
              fullWidth
            />
          </Grid>

          <Grid size={{ xs: 12, md: 3 }}>
            <TextField label="Top Margin (mm)" type="number" value={marginTop} onChange={(e) => setMarginTop(Number(e.target.value || 0))} fullWidth />
          </Grid>
          <Grid size={{ xs: 12, md: 3 }}>
            <TextField label="Bottom Margin (mm)" type="number" value={marginBottom} onChange={(e) => setMarginBottom(Number(e.target.value || 0))} fullWidth />
          </Grid>
          <Grid size={{ xs: 12, md: 3 }}>
            <TextField label="Left Margin (mm)" type="number" value={marginLeft} onChange={(e) => setMarginLeft(Number(e.target.value || 0))} fullWidth />
          </Grid>
          <Grid size={{ xs: 12, md: 3 }}>
            <TextField label="Right Margin (mm)" type="number" value={marginRight} onChange={(e) => setMarginRight(Number(e.target.value || 0))} fullWidth />
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <TextField label="Watermark" value={watermark} onChange={(event) => setWatermark(event.target.value)} fullWidth />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <TextField label="Font Family" value={fontFamily} onChange={(event) => setFontFamily(event.target.value)} fullWidth />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <InputLabel id="variable-mode-label">Variable Resolution Mode</InputLabel>
            <Select
              labelId="variable-mode-label"
              value={variableMode}
              onChange={(event) => setVariableMode(event.target.value as TemplatePdfVariableResolutionMode)}
              fullWidth
            >
              <MenuItem value="RESOLVE_STRICT">Resolve Strict (Final)</MenuItem>
              <MenuItem value="KEEP_UNRESOLVED">Keep Unresolved (Preview)</MenuItem>
            </Select>
          </Grid>

          <Grid size={{ xs: 12, md: 3 }}>
            <FormControlLabel
              control={<Switch checked={includeHeaderFooter} onChange={(event) => setIncludeHeaderFooter(event.target.checked)} />}
              label="Include Header/Footer"
            />
          </Grid>
          <Grid size={{ xs: 12, md: 3 }}>
            <FormControlLabel
              control={<Switch checked={includePageNumbers} onChange={(event) => setIncludePageNumbers(event.target.checked)} />}
              label="Include Page Numbers"
            />
          </Grid>
          <Grid size={{ xs: 12, md: 3 }}>
            <FormControlLabel
              control={<Switch checked={fontEmbedding} onChange={(event) => setFontEmbedding(event.target.checked)} />}
              label="Font Embedding"
            />
          </Grid>
          <Grid size={{ xs: 12, md: 3 }}>
            <TextField label="Output File Name" value={fileName} onChange={(event) => setFileName(event.target.value)} fullWidth />
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <TextField
              label="PDF Password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              fullWidth
            />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <FormControlLabel
              control={<Switch checked={restrictPrinting} onChange={(event) => setRestrictPrinting(event.target.checked)} />}
              label="Print Restriction"
            />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <FormControlLabel
              control={<Switch checked={restrictCopy} onChange={(event) => setRestrictCopy(event.target.checked)} />}
              label="Copy Restriction"
            />
          </Grid>
        </Grid>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Runtime Input</Typography>
        <Stack spacing={2}>
          <TextField
            label="Variables JSON"
            value={variablesText}
            onChange={(event) => setVariablesText(event.target.value)}
            multiline
            minRows={6}
            fullWidth
          />
          <TextField
            label="PDF Metadata JSON"
            value={metadataText}
            onChange={(event) => setMetadataText(event.target.value)}
            multiline
            minRows={4}
            fullWidth
          />
        </Stack>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>Output Options</Typography>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.5}>
          <Button
            variant="contained"
            startIcon={<VisibilityOutlinedIcon />}
            disabled={!isApproved || previewMutation.isPending}
            onClick={handlePreview}
          >
            {previewMutation.isPending ? 'Generating Preview...' : 'Preview PDF'}
          </Button>
          <Button
            variant="contained"
            color="secondary"
            startIcon={<DownloadOutlinedIcon />}
            disabled={!isApproved || generateMutation.isPending}
            onClick={() => handleGenerate(false)}
          >
            {generateMutation.isPending ? 'Generating...' : 'Download PDF'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<PrintOutlinedIcon />}
            disabled={!previewSrc}
            onClick={handlePrint}
          >
            Print
          </Button>
          <Button
            variant="outlined"
            startIcon={<SaveOutlinedIcon />}
            disabled={!isApproved || generateMutation.isPending}
            onClick={() => handleGenerate(true)}
          >
            Save Copy
          </Button>
          <Button
            variant="text"
            startIcon={<PictureAsPdfOutlinedIcon />}
            disabled={!isApproved}
            onClick={() => window.open(latestApprovedDownloadUrl, '_blank', 'noopener,noreferrer')}
          >
            Quick Download (Latest Approved)
          </Button>
        </Stack>

        {previewMutation.error ? (
          <Alert severity="error" sx={{ mt: 2 }}>
            {getApiErrorMessage(previewMutation.error, 'Preview failed.')}
          </Alert>
        ) : null}

        {generateMutation.error ? (
          <Alert severity="error" sx={{ mt: 2 }}>
            {getApiErrorMessage(generateMutation.error, 'Generation failed.')}
          </Alert>
        ) : null}

        {previewData?.missing_variables?.length ? (
          <Alert severity="warning" sx={{ mt: 2 }}>
            Missing variables: {previewData.missing_variables.join(', ')}
          </Alert>
        ) : null}

        {previewData?.warnings?.length ? (
          <Alert severity="info" sx={{ mt: 2 }}>
            {previewData.warnings.join(' | ')}
          </Alert>
        ) : null}
      </Paper>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>PDF Preview</Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Preview and final generation use the same ProseMirror-based rendering engine.
        </Typography>

        {previewSrc ? (
          <Box sx={{ border: '1px solid', borderColor: 'divider', borderRadius: 1, overflow: 'hidden', height: { xs: 480, md: 780 } }}>
            <iframe
              title="Enterprise PDF Preview"
              src={previewSrc}
              style={{ border: 0, width: '100%', height: '100%' }}
            />
          </Box>
        ) : (
          <EmptyState
            title="No preview available"
            description="Run Preview PDF to inspect pagination and rendering before final download."
          />
        )}
      </Paper>
    </Stack>
  );
}
