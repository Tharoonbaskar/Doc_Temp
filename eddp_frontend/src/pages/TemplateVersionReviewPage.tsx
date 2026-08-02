import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Button,
  Stack,
  Typography,
  Alert,
  CircularProgress,
  Card,
  CardContent,
  Chip,
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import WarningAmberIcon from '@mui/icons-material/WarningAmber';

import { PageHeader } from '../components/common/PageHeader';
import { LoadingOverlay } from '../components/common/LoadingOverlay';
import { ElementDiffView } from '../features/templates/components/ElementDiffView';
import { useVersionChanges, useReviewElementChange, useApproveDraftVersion } from '../features/templates/hooks/useTemplates';
import type { ReviewAction } from '../features/templates/types';
import { TEMPLATE_APPROVAL_ROUTES } from '../constants/appConstants';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';
import { getApiErrorMessage } from '../utils/apiErrorMessage';

export function TemplateVersionReviewPage() {
  const { id, versionNumber } = useParams<{ id: string; versionNumber: string }>();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [reviewComment, setReviewComment] = useState('');

  const versionNum = parseInt(versionNumber || '0', 10);
  const changesQuery = useVersionChanges(id!, versionNum, Boolean(id && versionNum > 0));
  const reviewMutation = useReviewElementChange();
  const approveMutation = useApproveDraftVersion();

  const handleReviewChange = async (changeId: string, action: ReviewAction) => {
    try {
      await reviewMutation.mutateAsync({ changeId, payload: { action, comment: reviewComment } });
      dispatch(enqueueNotification({ severity: 'success', message: `Change ${action.toLowerCase()} successfully` }));
      setReviewComment('');
    } catch (error) {
      dispatch(enqueueNotification({ 
        severity: 'error', 
        message: getApiErrorMessage(error, 'Failed to review change') 
      }));
    }
  };

  const handleApproveVersion = async () => {
    try {
      await approveMutation.mutateAsync({ templateId: id!, versionNumber: versionNum });
      dispatch(enqueueNotification({ severity: 'success', message: 'Version approved successfully' }));
      navigate(TEMPLATE_APPROVAL_ROUTES.LIST);
    } catch (error: any) {
      dispatch(enqueueNotification({ 
        severity: 'error', 
        message: getApiErrorMessage(error, 'Failed to approve version') 
      }));
    }
  };

  if (changesQuery.isLoading) {
    return <LoadingOverlay open />;
  }

  if (changesQuery.isError || !changesQuery.data) {
    return (
      <Box p={3}>
        <Alert severity="error">Failed to load version changes. Please try again.</Alert>
      </Box>
    );
  }

  const { version, changes, diff_summary } = changesQuery.data;
  
  const pendingCount = changes.filter(c => c.approval_status === 'PENDING').length;
  const approvedCount = changes.filter(c => c.approval_status === 'APPROVED').length;
  const rejectedCount = changes.filter(c => c.approval_status === 'REJECTED').length;
  const allReviewed = pendingCount === 0;

  return (
    <Box>
      <PageHeader
        title={`Review Version ${version.version_name}`}
        subtitle={version.change_summary}
      />

      <Box p={3}>
        <Stack spacing={3}>
          {/* Version Info Card */}
          <Card>
            <CardContent>
              <Stack spacing={2}>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="h6">Version Summary</Typography>
                  <Chip 
                    label={version.version_status} 
                    color={version.version_status === 'DRAFT' ? 'warning' : 'success'} 
                  />
                </Box>
                
                <Divider />

                <Stack direction="row" spacing={3}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Total Changes</Typography>
                    <Typography variant="h4">{diff_summary.total_changes}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Added</Typography>
                    <Typography variant="h4" color="success.main">{diff_summary.added}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Modified</Typography>
                    <Typography variant="h4" color="warning.main">{diff_summary.modified}</Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Deleted</Typography>
                    <Typography variant="h4" color="error.main">{diff_summary.deleted}</Typography>
                  </Box>
                </Stack>

                <Divider />

                <Stack direction="row" spacing={3}>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Approved</Typography>
                    <Typography variant="body1" color="success.main" fontWeight="medium">
                      {approvedCount}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Rejected</Typography>
                    <Typography variant="body1" color="error.main" fontWeight="medium">
                      {rejectedCount}
                    </Typography>
                  </Box>
                  <Box>
                    <Typography variant="caption" color="text.secondary">Pending</Typography>
                    <Typography variant="body1" color="warning.main" fontWeight="medium">
                      {pendingCount}
                    </Typography>
                  </Box>
                </Stack>
              </Stack>
            </CardContent>
          </Card>

          {/* Status Alert */}
          {allReviewed ? (
            <Alert 
              severity="success" 
              icon={<CheckCircleIcon />}
              action={
                <Button 
                  color="inherit" 
                  size="small" 
                  onClick={handleApproveVersion}
                  disabled={approveMutation.isPending}
                >
                  {approveMutation.isPending ? <CircularProgress size={20} /> : 'Approve Version'}
                </Button>
              }
            >
              All changes have been reviewed. You can now approve this version.
            </Alert>
          ) : (
            <Alert severity="warning" icon={<WarningAmberIcon />}>
              {pendingCount} change(s) still pending review. Please review all changes before approving.
            </Alert>
          )}

          {/* Changes List */}
          <Box>
            <Typography variant="h6" gutterBottom>
              Element Changes
            </Typography>
            {changes.length === 0 ? (
              <Alert severity="info">No changes in this version.</Alert>
            ) : (
              changes.map((change) => (
                <ElementDiffView
                  key={change.id}
                  change={change}
                  onReview={handleReviewChange}
                  disabled={reviewMutation.isPending}
                />
              ))
            )}
          </Box>

          {/* Actions */}
          <Stack direction="row" spacing={2} justifyContent="space-between">
            <Button
              variant="outlined"
              startIcon={<ArrowBackIcon />}
              onClick={() => navigate(TEMPLATE_APPROVAL_ROUTES.LIST)}
            >
              Back to Approvals
            </Button>
            
            {allReviewed && (
              <Button
                variant="contained"
                color="success"
                startIcon={<CheckCircleIcon />}
                onClick={handleApproveVersion}
                disabled={approveMutation.isPending}
              >
                {approveMutation.isPending ? 'Approving...' : 'Approve Version'}
              </Button>
            )}
          </Stack>
        </Stack>
      </Box>

      {/* Review Comment Dialog */}
      <Dialog open={reviewDialogOpen} onClose={() => setReviewDialogOpen(false)}>
        <DialogTitle>Add Review Comment</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            rows={4}
            label="Comment (Optional)"
            value={reviewComment}
            onChange={(e) => setReviewComment(e.target.value)}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReviewDialogOpen(false)}>Cancel</Button>
          <Button onClick={() => setReviewDialogOpen(false)} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
