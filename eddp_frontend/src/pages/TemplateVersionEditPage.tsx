import { Alert, Box, Button, Chip, Stack } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { LoadingOverlay } from '../components/common/LoadingOverlay';
import { PageHeader } from '../components/common/PageHeader';
import { TEMPLATE_APPROVAL_ROUTES, TEMPLATE_ROUTES } from '../constants/appConstants';
import { TemplateForm } from '../features/templates/components/TemplateForm';
import {
  useTemplateVersionDetail,
  useUpdateDraftVersion,
  useSendDraftVersionForReview,
  useVersionChanges,
  useReviewElementChange,
  useApproveDraftVersion,
} from '../features/templates/hooks/useTemplates';
import type { ReviewAction, TemplatePayload } from '../features/templates/types';
import { useDocuments } from '../features/documents/hooks/useDocuments';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';
import { getApiErrorMessage } from '../utils/apiErrorMessage';

export function TemplateVersionEditPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { id = '', versionNumber = '0' } = useParams();

  const versionNum = Number(versionNumber);
  const detailQuery = useTemplateVersionDetail(id, versionNum, Boolean(id && versionNum > 0));
  const documentsQuery = useDocuments();
  const updateDraftMutation = useUpdateDraftVersion();
  const sendForReviewMutation = useSendDraftVersionForReview();
  const changesQuery = useVersionChanges(id, versionNum, Boolean(id && versionNum > 0));
  const reviewChangeMutation = useReviewElementChange();
  const approveVersionMutation = useApproveDraftVersion();

  if (detailQuery.isLoading) {
    return <LoadingOverlay open />;
  }

  if (detailQuery.error || !detailQuery.data) {
    return <Alert severity="error">Failed to load version details.</Alert>;
  }

  const { template, version } = detailQuery.data;

  const versionChanges = changesQuery.data?.changes ?? [];
  const pendingCount = versionChanges.filter((change) => change.approval_status === 'PENDING').length;
  const approvedCount = versionChanges.filter((change) => change.approval_status === 'APPROVED').length;
  const rejectedCount = versionChanges.filter((change) => change.approval_status === 'REJECTED').length;
  const canApproveVersion = version.version_status === 'FOR_REVIEW' && pendingCount === 0 && versionChanges.length > 0;

  const canonicalEmptyDoc = {
    type: 'doc',
    content: [{ type: 'paragraph' }],
  } as const;

  const versionDocObject =
    typeof version.template_json === 'object' && version.template_json !== null
      ? (version.template_json as Record<string, unknown>)
      : null;

  const versionProsemirrorJson =
    versionDocObject?.type === 'doc'
      ? versionDocObject
      : (versionDocObject?.prosemirror_json as Record<string, unknown> | undefined);

  const initialValue: TemplatePayload = {
    code: template.code,
    name: template.name,
    description: template.description,
    category: template.category,
    document_id: template.document?.id ?? template.document_id ?? '',
    template_type: template.template_type,
    content_type: template.content_type,
    prosemirror_json: versionProsemirrorJson,
    page_size: template.page_size,
    page_orientation: template.page_orientation,
    is_default: template.is_default,
    status: template.status,
  };

  if (version.version_status !== 'DRAFT' && version.version_status !== 'FOR_REVIEW') {
    return (
      <EmptyState
        title="Version not editable"
        description="Only in-progress versions can be opened in the template editor."
      />
    );
  }

  const handleSendForReview = async (payload: TemplatePayload) => {
    try {
      await updateDraftMutation.mutateAsync({
        templateId: id,
        versionNumber: versionNum,
        prosemirrorJson: payload.prosemirror_json ?? canonicalEmptyDoc,
        pageSize: payload.page_size,
        pageOrientation: payload.page_orientation,
      });
      await sendForReviewMutation.mutateAsync({ templateId: id, versionNumber: versionNum });
      dispatch(enqueueNotification({ severity: 'success', message: `Version v${versionNum}.0 sent for review.` }));
      navigate(TEMPLATE_APPROVAL_ROUTES.LIST);
    } catch (error) {
      dispatch(enqueueNotification({
        severity: 'error',
        message: getApiErrorMessage(error, 'Failed to send version for review.'),
      }));
    }
  };

  const handleReviewChange = async (changeId: string, action: ReviewAction, comment?: string) => {
    try {
      await reviewChangeMutation.mutateAsync({ changeId, payload: { action, comment } });
      dispatch(enqueueNotification({ severity: 'success', message: `Change ${action.toLowerCase()} successfully.` }));
    } catch (error) {
      dispatch(enqueueNotification({
        severity: 'error',
        message: getApiErrorMessage(error, 'Failed to review change.'),
      }));
    }
  };

  const handleApproveVersion = async () => {
    if (pendingCount > 0) {
      dispatch(enqueueNotification({
        severity: 'warning',
        message: `${pendingCount} change(s) are still pending review.`,
      }));
      return;
    }

    try {
      await approveVersionMutation.mutateAsync({ templateId: id, versionNumber: versionNum });
      dispatch(enqueueNotification({ severity: 'success', message: `Version v${versionNum}.0 approved.` }));
      navigate(TEMPLATE_APPROVAL_ROUTES.LIST);
    } catch (error) {
      dispatch(enqueueNotification({
        severity: 'error',
        message: getApiErrorMessage(error, 'Failed to approve version.'),
      }));
    }
  };

  return (
    <Stack spacing={3}>
      <PageHeader
        title={`Edit Version v${versionNum}.0`}
        subtitle={`${template.name} - continue editing draft changes in template editor`}
      />

      {(updateDraftMutation.error || sendForReviewMutation.error) ? (
        <Alert severity="error">
          {getApiErrorMessage(updateDraftMutation.error || sendForReviewMutation.error, 'Operation failed.')}
        </Alert>
      ) : null}

      {version.version_status === 'FOR_REVIEW' ? (
        <Alert severity={pendingCount === 0 ? 'success' : 'warning'}>
          <Stack direction="row" spacing={2} alignItems="center" justifyContent="space-between">
            <Stack direction="row" spacing={1} alignItems="center">
              <Chip label={`Approved: ${approvedCount}`} color="success" size="small" />
              <Chip label={`Rejected: ${rejectedCount}`} color="error" size="small" variant="outlined" />
              <Chip label={`Pending: ${pendingCount}`} color="warning" size="small" />
            </Stack>
            <Button
              variant="contained"
              color="success"
              onClick={handleApproveVersion}
              disabled={!canApproveVersion || approveVersionMutation.isPending}
            >
              {approveVersionMutation.isPending ? 'Approving...' : `Approve v${versionNum}.0`}
            </Button>
          </Stack>
        </Alert>
      ) : null}

      {version.version_status === 'FOR_REVIEW' ? (
        <Box sx={{ flex: 1, minWidth: 0 }}>
          {changesQuery.isLoading ? <Alert severity="info">Loading changes...</Alert> : null}
          {(!changesQuery.isLoading && versionChanges.length === 0) ? (
            <Alert severity="warning">No tracked changes found for this version.</Alert>
          ) : null}

          <TemplateForm
            initialValue={initialValue}
            documents={documentsQuery.data ?? []}
            templateStatus="FOR_REVIEW"
            currentVersion={version.version_number}
            versionCount={template.version_count}
            readOnly
            reviewChanges={versionChanges}
            versionLabel={`v${version.version_number}.0`}
            documentId={id}
            onReviewChange={handleReviewChange}
            reviewActionsDisabled={reviewChangeMutation.isPending || approveVersionMutation.isPending}
            onSubmit={async (payload) => {
              await updateDraftMutation.mutateAsync({
                templateId: id,
                versionNumber: versionNum,
                prosemirrorJson: payload.prosemirror_json ?? canonicalEmptyDoc,
                pageSize: payload.page_size,
                pageOrientation: payload.page_orientation,
              });
              dispatch(enqueueNotification({ severity: 'success', message: `Draft v${versionNum}.0 updated.` }));
              navigate(TEMPLATE_ROUTES.editVersion(id, versionNum));
            }}
            onSendForReview={undefined}
            onApprove={handleApproveVersion}
          />
        </Box>
      ) : (
        <TemplateForm
          initialValue={initialValue}
          documents={documentsQuery.data ?? []}
          templateStatus="DRAFT"
          currentVersion={version.version_number}
          versionCount={template.version_count}
          reviewChanges={versionChanges}
          versionLabel={`v${version.version_number}.0`}
          documentId={id}
          onSubmit={async (payload) => {
            await updateDraftMutation.mutateAsync({
              templateId: id,
              versionNumber: versionNum,
              prosemirrorJson: payload.prosemirror_json ?? canonicalEmptyDoc,
              pageSize: payload.page_size,
              pageOrientation: payload.page_orientation,
            });
            dispatch(enqueueNotification({ severity: 'success', message: `Draft v${versionNum}.0 updated.` }));
            navigate(TEMPLATE_ROUTES.editVersion(id, versionNum));
          }}
          onSendForReview={handleSendForReview}
          onApprove={undefined}
        />
      )}
    </Stack>
  );
}
