import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import { Alert, Button, Paper, Stack, Typography } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { LoadingOverlay } from '../components/common/LoadingOverlay';
import { PageHeader } from '../components/common/PageHeader';
import { CONNECTOR_ROUTES } from '../constants/appConstants';
import { useConnector } from '../features/connectors/hooks/useConnectors';

export function ConnectorViewPage() {
  const navigate = useNavigate();
  const { id = '' } = useParams();
  const query = useConnector(id);

  if (query.isLoading) {
    return <LoadingOverlay open />;
  }

  if (query.error) {
    return <Alert severity="error">Failed to load connector details.</Alert>;
  }

  if (!query.data) {
    return <EmptyState title="Connector not found" description="The requested connector does not exist." />;
  }

  const row = query.data;

  return (
    <Stack spacing={3}>
      <PageHeader
        title={row.name}
        subtitle="Connector details"
        actions={
          <Button variant="contained" startIcon={<EditOutlinedIcon />} onClick={() => navigate(CONNECTOR_ROUTES.edit(row.id))}>
            Edit
          </Button>
        }
      />

      <Paper variant="outlined" sx={{ p: 3 }}>
        <Stack spacing={1}>
          <Typography><strong>Code:</strong> {row.code}</Typography>
          <Typography><strong>Status:</strong> {row.status}</Typography>
          <Typography><strong>Type:</strong> {row.connector_type}</Typography>
          <Typography><strong>Host:</strong> {row.host || '-'}</Typography>
          <Typography><strong>Port:</strong> {row.port ?? '-'}</Typography>
          <Typography><strong>API Base URL:</strong> {row.api_base_url || '-'}</Typography>
          <Typography><strong>Database Name:</strong> {row.database_name || '-'}</Typography>
          <Typography><strong>Timeout:</strong> {row.timeout}</Typography>
          <Typography><strong>Retry Count:</strong> {row.retry_count}</Typography>
          <Typography><strong>Active:</strong> {row.is_active ? 'Yes' : 'No'}</Typography>
          <Typography><strong>Description:</strong> {row.description || '-'}</Typography>
        </Stack>
      </Paper>
    </Stack>
  );
}
