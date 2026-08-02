import { Alert, Stack } from '@mui/material';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '../components/common/PageHeader';
import { WORKFLOW_ROUTES } from '../constants/appConstants';
import { useDocuments } from '../features/documents/hooks/useDocuments';
import { WorkflowForm } from '../features/workflow/components/WorkflowForm';
import { useCreateWorkflow, useWorkflowList } from '../features/workflow/hooks/useWorkflow';
import type { WorkflowPayload } from '../features/workflow/types';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';

export function WorkflowCreatePage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const mutation = useCreateWorkflow();
  const workflowQuery = useWorkflowList();
  const documentsQuery = useDocuments();

  const existingCodes = (workflowQuery.data ?? []).map((workflowItem) => workflowItem.code);
  const documents = documentsQuery.data ?? [];

  const handleCreate = async (payload: WorkflowPayload): Promise<void> => {
    const created = await mutation.mutateAsync(payload);
    dispatch(enqueueNotification({ severity: 'success', message: 'Workflow created.' }));
    navigate(WORKFLOW_ROUTES.view(created.id));
  };

  return (
    <Stack spacing={3}>
      <PageHeader title="Create Workflow" subtitle="Register a new workflow definition." />
      {mutation.error ? <Alert severity="error">Failed to create workflow.</Alert> : null}
      <WorkflowForm submitLabel="Create Workflow" existingCodes={existingCodes} documents={documents} onSubmit={handleCreate} />
    </Stack>
  );
}
