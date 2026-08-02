import { Alert, Stack } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { LoadingOverlay } from '../components/common/LoadingOverlay';
import { PageHeader } from '../components/common/PageHeader';
import { WORKFLOW_ROUTES } from '../constants/appConstants';
import { useDocuments } from '../features/documents/hooks/useDocuments';
import { WorkflowForm } from '../features/workflow/components/WorkflowForm';
import { useUpdateWorkflow, useWorkflow } from '../features/workflow/hooks/useWorkflow';
import type { WorkflowPayload } from '../features/workflow/types';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';

export function WorkflowEditPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { id = '' } = useParams();

  const query = useWorkflow(id);
  const documentsQuery = useDocuments();
  const mutation = useUpdateWorkflow();

  if (query.isLoading) {
    return <LoadingOverlay open />;
  }

  if (!query.data) {
    return <EmptyState title="Workflow not found" description="The requested workflow does not exist." />;
  }

  const documents = documentsQuery.data ?? [];

  const initialValue: WorkflowPayload = {
    code: query.data.code,
    name: query.data.name,
    description: query.data.description,
    workflow_type: query.data.workflow_type,
    applicable_document_id: query.data.applicable_document?.id ?? '',
    version: query.data.version,
    is_default: query.data.is_default,
    status: query.data.status,
  };

  return (
    <Stack spacing={3}>
      <PageHeader title="Edit Workflow" subtitle={`Update ${query.data.name}`} />
      {mutation.error ? <Alert severity="error">Failed to update workflow.</Alert> : null}
      <WorkflowForm
        initialValue={initialValue}
        documents={documents}
        submitLabel="Save Changes"
        onSubmit={async (payload) => {
          await mutation.mutateAsync({ id, payload });
          dispatch(enqueueNotification({ severity: 'success', message: 'Workflow updated.' }));
          navigate(WORKFLOW_ROUTES.view(id));
        }}
      />
    </Stack>
  );
}
