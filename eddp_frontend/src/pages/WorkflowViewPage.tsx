import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import { Alert, Button, Paper, Stack, Typography } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { LoadingOverlay } from '../components/common/LoadingOverlay';
import { PageHeader } from '../components/common/PageHeader';
import { WORKFLOW_ROUTES } from '../constants/appConstants';
import { useWorkflow } from '../features/workflow/hooks/useWorkflow';

export function WorkflowViewPage() {
  const navigate = useNavigate();
  const { id = '' } = useParams();
  const query = useWorkflow(id);

  if (query.isLoading) {
    return <LoadingOverlay open />;
  }

  if (query.error) {
    return <Alert severity="error">Failed to load workflow details.</Alert>;
  }

  if (!query.data) {
    return <EmptyState title="Workflow not found" description="The requested workflow does not exist." />;
  }

  const row = query.data;

  return (
    <Stack spacing={3}>
      <PageHeader
        title={row.name}
        subtitle="Workflow details"
        actions={
          <Button variant="contained" startIcon={<EditOutlinedIcon />} onClick={() => navigate(WORKFLOW_ROUTES.edit(row.id))}>
            Edit
          </Button>
        }
      />

      <Paper variant="outlined" sx={{ p: 3 }}>
        <Stack spacing={1}>
          <Typography><strong>Code:</strong> {row.code}</Typography>
          <Typography><strong>Status:</strong> {row.status}</Typography>
          <Typography><strong>Type:</strong> {row.workflow_type}</Typography>
          <Typography><strong>Document ID:</strong> {row.applicable_document?.id ?? '-'}</Typography>
          <Typography><strong>Document:</strong> {row.applicable_document?.name ?? '-'}</Typography>
          <Typography><strong>Version:</strong> {row.version}</Typography>
          <Typography><strong>Default:</strong> {row.is_default ? 'Yes' : 'No'}</Typography>
          <Typography><strong>Description:</strong> {row.description || '-'}</Typography>
        </Stack>
      </Paper>
    </Stack>
  );
}
