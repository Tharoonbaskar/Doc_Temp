import { Alert, Stack } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { LoadingOverlay } from '../components/common/LoadingOverlay';
import { PageHeader } from '../components/common/PageHeader';
import { VARIABLE_ROUTES } from '../constants/appConstants';
import { VariableForm } from '../features/variables/components/VariableForm';
import { useUpdateVariable, useVariable } from '../features/variables/hooks/useVariables';
import type { VariablePayload } from '../features/variables/types';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';

export function VariableEditPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { id = '' } = useParams();

  const query = useVariable(id);
  const mutation = useUpdateVariable();

  if (query.isLoading) {
    return <LoadingOverlay open />;
  }

  if (!query.data) {
    return <EmptyState title="Variable not found" description="The requested variable does not exist." />;
  }

  const initialValue: VariablePayload = {
    code: query.data.code,
    name: query.data.name,
    display_name: query.data.display_name,
    description: query.data.description,
    group_id: query.data.group?.id ?? query.data.group_id ?? '',
    data_type: query.data.data_type,
    source_type: query.data.source_type,
    source_reference: query.data.source_reference,
    default_value: query.data.default_value,
    is_required: query.data.is_required,
    document_ids: query.data.documents?.map((doc) => doc.id) || [],
    status: query.data.status,
  };

  return (
    <Stack spacing={3}>
      <PageHeader title="Edit Variable" subtitle={`Update ${query.data.display_name}`} />
      {mutation.error ? <Alert severity="error">Failed to update variable.</Alert> : null}
      <VariableForm
        initialValue={initialValue}
        submitLabel="Save Changes"
        onSubmit={async (payload) => {
          await mutation.mutateAsync({ id, payload });
          dispatch(enqueueNotification({ severity: 'success', message: 'Variable updated.' }));
          navigate(VARIABLE_ROUTES.view(id));
        }}
      />
    </Stack>
  );
}
