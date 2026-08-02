import { Alert, Stack } from '@mui/material';
import { useNavigate } from 'react-router-dom';

import { PageHeader } from '../components/common/PageHeader';
import { CONNECTOR_ROUTES } from '../constants/appConstants';
import { ConnectorForm } from '../features/connectors/components/ConnectorForm';
import { useConnectors, useCreateConnector } from '../features/connectors/hooks/useConnectors';
import type { ConnectorPayload } from '../features/connectors/types';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';

export function ConnectorCreatePage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const mutation = useCreateConnector();
  const connectorsQuery = useConnectors();

  const existingCodes = (connectorsQuery.data ?? []).map((connectorItem) => connectorItem.code);

  const handleCreate = async (payload: ConnectorPayload): Promise<void> => {
    const created = await mutation.mutateAsync(payload);
    dispatch(enqueueNotification({ severity: 'success', message: 'Connector created.' }));
    navigate(CONNECTOR_ROUTES.view(created.id));
  };

  return (
    <Stack spacing={3}>
      <PageHeader title="Create Connector" subtitle="Register a new integration connector." />
      {mutation.error ? <Alert severity="error">Failed to create connector.</Alert> : null}
      <ConnectorForm submitLabel="Create Connector" existingCodes={existingCodes} onSubmit={handleCreate} />
    </Stack>
  );
}
