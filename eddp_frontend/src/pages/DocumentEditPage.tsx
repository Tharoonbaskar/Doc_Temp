import { Alert, Stack } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { LoadingOverlay } from '../components/common/LoadingOverlay';
import { PageHeader } from '../components/common/PageHeader';
import { DOCUMENT_ROUTES } from '../constants/appConstants';
import { DocumentForm } from '../features/documents/components/DocumentForm';
import { useDocument, useUpdateDocument } from '../features/documents/hooks/useDocuments';
import type { DocumentPayload } from '../features/documents/types';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';
import { getApiErrorMessage } from '../utils/apiErrorMessage';

const ALLOWED_PRODUCTS = ['HOME LOAN', 'PLOT LOAN', 'LAP'] as const;

const isAllowedProduct = (value: string): value is (typeof ALLOWED_PRODUCTS)[number] =>
  (ALLOWED_PRODUCTS as readonly string[]).includes(value);

const normalizeProductValues = (value: string[] | string): DocumentPayload['product'] => {
  const values = Array.isArray(value)
    ? value
    : value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);

  return values.filter(isAllowedProduct);
};

export function DocumentEditPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { id = '' } = useParams();

  const query = useDocument(id);
  const mutation = useUpdateDocument();

  if (query.isLoading) {
    return <LoadingOverlay open />;
  }

  if (!query.data) {
    return <EmptyState title="Document not found" description="The requested document does not exist." />;
  }

  const initialValue: DocumentPayload = {
    code: query.data.code,
    name: query.data.name,
    description: query.data.description,
    category_id: query.data.category?.id ?? query.data.category_id ?? '',
    document_type: query.data.document_type,
    business_module: query.data.business_module,
    product: normalizeProductValues(query.data.product),
    output_format: query.data.output_format,
    status: query.data.status,
  };

  return (
    <Stack spacing={3}>
      <PageHeader title="Edit Document" subtitle={`Update ${query.data.name}`} />
      {mutation.error ? <Alert severity="error">{getApiErrorMessage(mutation.error, 'Failed to update document.')}</Alert> : null}
      <DocumentForm
        initialValue={initialValue}
        submitLabel="Save Changes"
        onSubmit={async (payload) => {
          await mutation.mutateAsync({ id, payload });
          dispatch(enqueueNotification({ severity: 'success', message: 'Document updated.' }));
          navigate(DOCUMENT_ROUTES.view(id));
        }}
      />
    </Stack>
  );
}
