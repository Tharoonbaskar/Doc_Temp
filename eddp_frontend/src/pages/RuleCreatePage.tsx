import { Alert, Stack } from '@mui/material';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '../components/common/PageHeader';
import { RULE_ROUTES } from '../constants/appConstants';
import { RuleForm } from '../features/rules/components/RuleForm';
import { useCreateRule, useRules } from '../features/rules/hooks/useRules';
import type { RulePayload } from '../features/rules/types';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';

export function RuleCreatePage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const mutation = useCreateRule();
  const rulesQuery = useRules();

  const existingCodes = (rulesQuery.data ?? []).map((ruleItem) => ruleItem.code);

  const handleCreate = async (payload: RulePayload): Promise<void> => {
    const created = await mutation.mutateAsync(payload);
    dispatch(enqueueNotification({ severity: 'success', message: 'Rule created.' }));
    navigate(RULE_ROUTES.view(created.id));
  };

  return (
    <Stack spacing={3}>
      <PageHeader title="Create Rule" subtitle="Register a new business rule." />
      {mutation.error ? <Alert severity="error">Failed to create rule.</Alert> : null}
      <RuleForm submitLabel="Create Rule" existingCodes={existingCodes} onSubmit={handleCreate} />
    </Stack>
  );
}
