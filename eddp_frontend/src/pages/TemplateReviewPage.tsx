import { Alert, Box, Button, Stack, TextField, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import CheckCircleOutlinedIcon from '@mui/icons-material/CheckCircleOutlined';
import UndoOutlinedIcon from '@mui/icons-material/UndoOutlined';
import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { LoadingOverlay } from '../components/common/LoadingOverlay';
import { PageHeader } from '../components/common/PageHeader';
import { ApproveTemplateDialog } from '../features/templates/components/ApproveTemplateDialog';
import { TemplateForm } from '../features/templates/components/TemplateForm';
import { useTemplate, useApproveTemplate, useSendBackTemplate } from '../features/templates/hooks/useTemplates';
import type { ApproveTemplatePayload, SendBackPayload, TemplatePayload } from '../features/templates/types';
import { useDocuments } from '../features/documents/hooks/useDocuments';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';
import { getApiErrorMessage } from '../utils/apiErrorMessage';
import { TEMPLATE_APPROVAL_ROUTES } from '../constants/appConstants';

export function TemplateReviewPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { id = '' } = useParams();
  
  const [approveDialogOpen, setApproveDialogOpen] = useState(false);
  const [sendBackDialogOpen, setSendBackDialogOpen] = useState(false);
  const [sendBackComments, setSendBackComments] = useState('');

  const query = useTemplate(id);
  const documentsQuery = useDocuments();
  const approveMutation = useApproveTemplate();
  const sendBackMutation = useSendBackTemplate();

  if (query.isLoading) {
    return <LoadingOverlay open />;
  }

  if (!query.data) {
    return <EmptyState title="Template not found" description="The requested template does not exist." />;
  }

  const isForReview = query.data.status === 'FOR_REVIEW';
  const isApproved = query.data.status === 'APPROVED';

  if (!isForReview && !isApproved) {
    return (
      <EmptyState 
        title="Not available for review" 
        description="This template is not in the approval workflow." 
      />
    );
  }

  const handleApprove = async (payload: ApproveTemplatePayload) => {
    try {
      await approveMutation.mutateAsync({ id, payload });
      dispatch(enqueueNotification({ severity: 'success', message: 'Template approved successfully.' }));
      navigate(TEMPLATE_APPROVAL_ROUTES.LIST);
    } catch (error) {
      dispatch(enqueueNotification({ 
        severity: 'error', 
        message: getApiErrorMessage(error, 'Failed to approve template.') 
      }));
    }
  };

  const handleSendBack = async () => {
    const payload: SendBackPayload = {
      comments: sendBackComments || undefined,
    };
    
    try {
      await sendBackMutation.mutateAsync({ id, payload });
      dispatch(enqueueNotification({ severity: 'success', message: 'Template sent back for revision.' }));
      setSendBackDialogOpen(false);
      navigate(TEMPLATE_APPROVAL_ROUTES.LIST);
    } catch (error) {
      dispatch(enqueueNotification({ 
        severity: 'error', 
        message: getApiErrorMessage(error, 'Failed to send template back.') 
      }));
    }
  };

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

  return (
    <Stack spacing={3}>
      <PageHeader 
        title={isApproved ? "View Approved Template" : "Review Template"} 
        subtitle={`Review ${query.data.name}`}
        actions={
          isForReview ? (
            <Stack direction="row" spacing={2}>
              <Button
                variant="outlined"
                color="warning"
                startIcon={<UndoOutlinedIcon />}
                onClick={() => setSendBackDialogOpen(true)}
              >
                Send Back
              </Button>
              <Button
                variant="contained"
                color="success"
                startIcon={<CheckCircleOutlinedIcon />}
                onClick={() => setApproveDialogOpen(true)}
              >
                Approve
              </Button>
            </Stack>
          ) : undefined
        }
      />

      {isApproved && (
        <Alert severity="success">
          <Stack spacing={1}>
            <Box><strong>Status:</strong> Approved</Box>
            <Box><strong>Version:</strong> v{query.data.current_version}.0</Box>
            {query.data.effective_date && (
              <Box><strong>Effective Date:</strong> {new Date(query.data.effective_date).toLocaleString()}</Box>
            )}
            {query.data.approved_by_name && (
              <Box><strong>Approved By:</strong> {query.data.approved_by_name}</Box>
            )}
            {query.data.approved_at && (
              <Box><strong>Approved At:</strong> {new Date(query.data.approved_at).toLocaleString()}</Box>
            )}
          </Stack>
        </Alert>
      )}

      {(approveMutation.error || sendBackMutation.error) && (
        <Alert severity="error">
          {getApiErrorMessage(approveMutation.error || sendBackMutation.error, 'An error occurred.')}
        </Alert>
      )}

      {/* Display template using TemplateForm in read-only mode */}
      <TemplateForm
        initialValue={initialValue}
        documents={documentsQuery.data ?? []}
        templateStatus={query.data.status}
        currentVersion={query.data.current_version}
        versionCount={query.data.version_count}
        onSubmit={async () => {
          // Read-only mode - no submit action
        }}
      />

      {/* Approve Dialog */}
      <ApproveTemplateDialog
        open={approveDialogOpen}
        onClose={() => setApproveDialogOpen(false)}
        onApprove={handleApprove}
        templateName={query.data.name}
      />

      {/* Send Back Dialog */}
      <Dialog open={sendBackDialogOpen} onClose={() => setSendBackDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Send Template Back for Revision</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ pt: 2 }}>
            <Alert severity="warning">
              This will return the template to the creator with DRAFT status for further revisions.
            </Alert>
            <TextField
              label="Comments (Optional)"
              value={sendBackComments}
              onChange={(e) => setSendBackComments(e.target.value)}
              multiline
              rows={4}
              fullWidth
              placeholder="Provide feedback or reasons for sending back..."
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSendBackDialogOpen(false)} color="inherit">
            Cancel
          </Button>
          <Button 
            onClick={handleSendBack}
            variant="contained" 
            color="warning"
          >
            Send Back
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}
