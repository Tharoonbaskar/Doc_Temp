import { Alert, Stack } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { LoadingOverlay } from '../components/common/LoadingOverlay';
import { PageHeader } from '../components/common/PageHeader';
import { RULE_ROUTES } from '../constants/appConstants';
import { RuleForm } from '../features/rules/components/RuleForm';
import { useRule, useUpdateRule } from '../features/rules/hooks/useRules';
import type { RulePayload } from '../features/rules/types';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';

export function RuleEditPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { id = '' } = useParams();

  const query = useRule(id);
  const mutation = useUpdateRule();

  if (query.isLoading) {
    return <LoadingOverlay open />;
  }

  if (!query.data) {
    return <EmptyState title="Rule not found" description="The requested rule does not exist." />;
  }

  const initialValue: RulePayload = {
    code: query.data.code,
    rule_group_id: query.data.rule_group_id ?? query.data.rule_group?.id ?? '',
    name: query.data.name,
    description: query.data.description,
    expression: query.data.expression,
    rule_type: query.data.rule_type,
    execution_order: query.data.execution_order,
    is_active: query.data.is_active,
    status: query.data.status,
  };

  return (
    <Stack spacing={3}>
      <PageHeader title="Edit Rule" subtitle={`Update ${query.data.name}`} />
      {mutation.error ? <Alert severity="error">Failed to update rule.</Alert> : null}
      <RuleForm
        initialValue={initialValue}
        submitLabel="Save Changes"
        onSubmit={async (payload) => {
          await mutation.mutateAsync({ id, payload });
          dispatch(enqueueNotification({ severity: 'success', message: 'Rule updated.' }));
          navigate(RULE_ROUTES.view(id));
        }}
      />
    </Stack>
  );
}
