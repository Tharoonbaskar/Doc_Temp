import { Alert, Stack } from '@mui/material';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '../components/common/PageHeader';
import { VARIABLE_ROUTES } from '../constants/appConstants';
import { VariableForm } from '../features/variables/components/VariableForm';
import { useCreateVariable, useVariables } from '../features/variables/hooks/useVariables';
import type { VariablePayload } from '../features/variables/types';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';

export function VariableCreatePage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const mutation = useCreateVariable();
  const variablesQuery = useVariables();

  const existingCodes = (variablesQuery.data ?? []).map((variableItem) => variableItem.code);

  const handleCreate = async (payload: VariablePayload): Promise<void> => {
    const created = await mutation.mutateAsync(payload);
    dispatch(enqueueNotification({ severity: 'success', message: 'Variable created.' }));
    navigate(VARIABLE_ROUTES.view(created.id));
  };

  return (
    <Stack spacing={3}>
      <PageHeader title="Create Variable" subtitle="Register a new variable definition." />
      {mutation.error ? <Alert severity="error">Failed to create variable.</Alert> : null}
      <VariableForm submitLabel="Create Variable" existingCodes={existingCodes} onSubmit={handleCreate} />
    </Stack>
  );
}
