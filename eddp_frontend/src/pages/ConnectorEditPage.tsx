import { Alert, Stack } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { LoadingOverlay } from '../components/common/LoadingOverlay';
import { PageHeader } from '../components/common/PageHeader';
import { CONNECTOR_ROUTES } from '../constants/appConstants';
import { ConnectorForm } from '../features/connectors/components/ConnectorForm';
import { useConnector, useUpdateConnector } from '../features/connectors/hooks/useConnectors';
import type { ConnectorPayload } from '../features/connectors/types';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';

export function ConnectorEditPage() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { id = '' } = useParams();

  const query = useConnector(id);
  const mutation = useUpdateConnector();

  if (query.isLoading) {
    return <LoadingOverlay open />;
  }

  if (!query.data) {
    return <EmptyState title="Connector not found" description="The requested connector does not exist." />;
  }

  const initialValue: ConnectorPayload = {
    code: query.data.code,
    name: query.data.name,
    connector_type: query.data.connector_type,
    description: query.data.description,
    host: query.data.host,
    port: query.data.port,
    database_name: query.data.database_name,
    username: query.data.username,
    password: '',
    api_base_url: query.data.api_base_url,
    timeout: query.data.timeout,
    retry_count: query.data.retry_count,
    is_active: query.data.is_active,
    status: query.data.status,
  };

  return (
    <Stack spacing={3}>
      <PageHeader title="Edit Connector" subtitle={`Update ${query.data.name}`} />
      {mutation.error ? <Alert severity="error">Failed to update connector.</Alert> : null}
      <ConnectorForm
        initialValue={initialValue}
        submitLabel="Save Changes"
        onSubmit={async (payload) => {
          await mutation.mutateAsync({ id, payload });
          dispatch(enqueueNotification({ severity: 'success', message: 'Connector updated.' }));
          navigate(CONNECTOR_ROUTES.view(id));
        }}
      />
    </Stack>
  );
}
