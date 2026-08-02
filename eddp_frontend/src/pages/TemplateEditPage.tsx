import { Alert, Stack } from '@mui/material';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { LoadingOverlay } from '../components/common/LoadingOverlay';
import { PageHeader } from '../components/common/PageHeader';
import { TEMPLATE_ROUTES } from '../constants/appConstants';
import { TemplateForm } from '../features/templates/components/TemplateForm';
import { ApproveTemplateDialog } from '../features/templates/components/ApproveTemplateDialog';
import { useDocuments } from '../features/documents/hooks/useDocuments';
import {
  useTemplate,
  useUpdateTemplate,
  useSendTemplateForReview,
  useApproveTemplate,
} from '../features/templates/hooks/useTemplates';
import type { TemplatePayload, ApproveTemplatePayload } from '../features/templates/types';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';
import { getApiErrorMessage } from '../utils/apiErrorMessage';

const getCreatedDraftVersionNumber = (response: unknown): number | null => {
  if (!response || typeof response !== 'object') {
    return null;
  }

  const record = response as Record<string, unknown>;
  const version = record.version;
  if (!version || typeof version !== 'object') {
    return null;
  }

  const versionRecord = version as Record<string, unknown>;
  const rawVersionNumber = versionRecord.version_number;
  return typeof rawVersionNumber === 'number' && rawVersionNumber > 0
    ? rawVersionNumber
    : null;
};

export function TemplateEditPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { id = '' } = useParams();
  const [approveDialogOpen, setApproveDialogOpen] = useState(false);

  const query = useTemplate(id);
  const documentsQuery = useDocuments();
  const updateMutation = useUpdateTemplate();
  const sendForReviewMutation = useSendTemplateForReview();
  const approveMutation = useApproveTemplate();

  if (query.isLoading) {
    return <LoadingOverlay open />;
  }

  if (!query.data) {
    return <EmptyState title="Template not found" description="The requested template does not exist." />;
  }

  if (query.data.has_pending_draft && query.data.pending_draft_version) {
    navigate(TEMPLATE_ROUTES.editVersion(id, query.data.pending_draft_version), { replace: true });
    return <LoadingOverlay open />;
  }

  // Redirect to review page if template is in FOR_REVIEW status
  if (query.data.status === 'FOR_REVIEW') {
    navigate(TEMPLATE_ROUTES.review(id), { replace: true });
    return <LoadingOverlay open />;
  }

  const initialValue: TemplatePayload = {
    code: query.data.code,
    name: query.data.name,
    description: query.data.description,
    category: query.data.category,
    document_id: query.data.document?.id ?? query.data.document_id ?? '',
    template_type: query.data.template_type,
    content_type: query.data.content_type,
    prosemirror_json: query.data.prosemirror_json,
    page_size: query.data.page_size,
    page_orientation: query.data.page_orientation,
    is_default: query.data.is_default,
    status: query.data.status,
  };

  const handleSendForReview = async (payload: TemplatePayload) => {
    try {
      await updateMutation.mutateAsync({ id, payload });
      await sendForReviewMutation.mutateAsync({ id, payload: {} });
      dispatch(enqueueNotification({ severity: 'success', message: 'Template sent for review.' }));
      navigate(TEMPLATE_ROUTES.review(id));
    } catch (error) {
      dispatch(enqueueNotification({ 
        severity: 'error', 
        message: getApiErrorMessage(error, 'Failed to send template for review.') 
      }));
    }
  };

  const handleApprove = async (payload: ApproveTemplatePayload) => {
    try {
      await approveMutation.mutateAsync({ id, payload });
      dispatch(enqueueNotification({ severity: 'success', message: 'Template approved successfully.' }));
      setApproveDialogOpen(false);
    } catch (error) {
      dispatch(enqueueNotification({ 
        severity: 'error', 
        message: getApiErrorMessage(error, 'Failed to approve template.') 
      }));
    }
  };

  return (
    <Stack spacing={3}>
      <PageHeader title="Edit Template" subtitle={`Update ${query.data.name}`} />
      {updateMutation.error ? (
        <Alert severity="error">{getApiErrorMessage(updateMutation.error, 'Failed to update template.')}</Alert>
      ) : null}
      <TemplateForm
        initialValue={initialValue}
        documents={documentsQuery.data ?? []}
        templateStatus={query.data.status}
        currentVersion={query.data.current_version}
        versionCount={query.data.version_count}
        onSubmit={async (payload) => {
          const result = await updateMutation.mutateAsync({ id, payload });
          const draftVersionNumber = getCreatedDraftVersionNumber(result);

          if (draftVersionNumber) {
            dispatch(enqueueNotification({
              severity: 'success',
              message: `Draft v${draftVersionNumber}.0 created. Continue changes in version editor.`,
            }));
            navigate(TEMPLATE_ROUTES.editVersion(id, draftVersionNumber));
            return;
          }

          dispatch(enqueueNotification({ severity: 'success', message: 'Template updated.' }));
          navigate(TEMPLATE_ROUTES.view(id));
        }}
        onSendForReview={handleSendForReview}
        onApprove={() => setApproveDialogOpen(true)}
      />
      
      <ApproveTemplateDialog
        open={approveDialogOpen}
        onClose={() => setApproveDialogOpen(false)}
        onApprove={handleApprove}
        templateName={query.data.name}
      />
    </Stack>
  );
}
