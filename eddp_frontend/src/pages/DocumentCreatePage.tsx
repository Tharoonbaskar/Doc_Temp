import { Alert, Stack } from '@mui/material';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '../components/common/PageHeader';
import { DOCUMENT_ROUTES } from '../constants/appConstants';
import { DocumentForm } from '../features/documents/components/DocumentForm';
import { useCreateDocument, useDocuments } from '../features/documents/hooks/useDocuments';
import type { DocumentPayload } from '../features/documents/types';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';
import { getApiErrorMessage } from '../utils/apiErrorMessage';

export function DocumentCreatePage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const mutation = useCreateDocument();
  const documentsQuery = useDocuments();

  const existingCodes = (documentsQuery.data ?? []).map((documentItem) => documentItem.code);

  const handleCreate = async (payload: DocumentPayload): Promise<void> => {
    const created = await mutation.mutateAsync(payload);
    dispatch(enqueueNotification({ severity: 'success', message: 'Document created.' }));
    navigate(DOCUMENT_ROUTES.view(created.id));
  };

  return (
    <Stack spacing={3}>
      <PageHeader title="Create Document" subtitle="Register a new document definition." />
      {mutation.error ? <Alert severity="error">{getApiErrorMessage(mutation.error, 'Failed to create document.')}</Alert> : null}
      <DocumentForm submitLabel="Create Document" existingCodes={existingCodes} onSubmit={handleCreate} />
    </Stack>
  );
}
