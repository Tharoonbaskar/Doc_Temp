import { Alert, Stack } from '@mui/material';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '../components/common/PageHeader';
import { TEMPLATE_ROUTES } from '../constants/appConstants';
import { TemplateForm } from '../features/templates/components/TemplateForm';
import { useDocuments } from '../features/documents/hooks/useDocuments';
import { useCreateTemplate, useTemplates } from '../features/templates/hooks/useTemplates';
import type { TemplatePayload, TemplateItem } from '../features/templates/types';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';
import { getApiErrorMessage } from '../utils/apiErrorMessage';

export function TemplateCreatePage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const mutation = useCreateTemplate();
  const templatesQuery = useTemplates();
  const documentsQuery = useDocuments();

  const existingCodes = (templatesQuery.data ?? []).map((templateItem: TemplateItem) => templateItem.code);
  const documents = documentsQuery.data ?? [];

  const handleCreate = async (payload: TemplatePayload): Promise<void> => {
    const created = await mutation.mutateAsync(payload);
    dispatch(enqueueNotification({ severity: 'success', message: 'Template created.' }));
    navigate(TEMPLATE_ROUTES.view(created.id));
  };

  return (
    <Stack spacing={3}>
      <PageHeader title="Create Template" subtitle="Register a new template." />
      {mutation.error ? <Alert severity="error">{getApiErrorMessage(mutation.error, 'Failed to create template.')}</Alert> : null}
      <TemplateForm
        existingCodes={existingCodes}
        documents={documents}
        onSubmit={handleCreate}
      />
    </Stack>
  );
}
