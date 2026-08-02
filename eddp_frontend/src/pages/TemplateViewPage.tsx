import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import PictureAsPdfOutlinedIcon from '@mui/icons-material/PictureAsPdfOutlined';
import { Alert, Button, Stack } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { LoadingOverlay } from '../components/common/LoadingOverlay';
import { PageHeader } from '../components/common/PageHeader';
import { TEMPLATE_ROUTES } from '../constants/appConstants';
import { useTemplate } from '../features/templates/hooks/useTemplates';
import { TemplateForm } from '../features/templates/components/TemplateForm';
import { useDocuments } from '../features/documents/hooks/useDocuments';
import type { TemplatePayload } from '../features/templates/types';

export function TemplateViewPage() {
  const navigate = useNavigate();
  const { id = '' } = useParams();
  const query = useTemplate(id);
  const documentsQuery = useDocuments();

  if (query.isLoading) {
    return <LoadingOverlay open />;
  }

  if (query.error) {
    return <Alert severity="error">Failed to load template details.</Alert>;
  }

  if (!query.data) {
    return <EmptyState title="Template not found" description="The requested template does not exist." />;
  }

  const row = query.data;

  const initialValue: TemplatePayload = {
    code: row.code,
    name: row.name,
    description: row.description,
    category: row.category,
    document_id: row.document?.id ?? row.document_id ?? '',
    template_type: row.template_type,
    content_type: row.content_type,
    prosemirror_json: row.prosemirror_json,
    page_size: row.page_size,
    page_orientation: row.page_orientation,
    is_default: row.is_default,
    status: row.status,
  };

  return (
    <Stack spacing={3}>
      <PageHeader
        title={row.name}
        subtitle="Template details"
        actions={
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={<PictureAsPdfOutlinedIcon />}
              onClick={() => navigate(TEMPLATE_ROUTES.pdfStudio(row.id))}
              disabled={row.status !== 'APPROVED'}
            >
              PDF Studio
            </Button>
            <Button
              variant="contained"
              startIcon={<EditOutlinedIcon />}
              onClick={() => {
                if (row.has_pending_draft && row.pending_draft_version) {
                  navigate(TEMPLATE_ROUTES.editVersion(row.id, row.pending_draft_version));
                  return;
                }
                navigate(TEMPLATE_ROUTES.edit(row.id));
              }}
            >
              Edit
            </Button>
          </Stack>
        }
      />

      <TemplateForm
        initialValue={initialValue}
        documents={documentsQuery.data ?? []}
        readOnly
        templateStatus={row.status}
        currentVersion={row.current_version}
        versionCount={row.version_count}
        onSubmit={async () => {
          // Read-only mode - no submit action
        }}
      />
    </Stack>
  );
}
