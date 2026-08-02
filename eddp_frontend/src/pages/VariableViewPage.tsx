import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import { Alert, Button, Paper, Stack, Typography } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { LoadingOverlay } from '../components/common/LoadingOverlay';
import { PageHeader } from '../components/common/PageHeader';
import { VARIABLE_ROUTES } from '../constants/appConstants';
import { useVariable } from '../features/variables/hooks/useVariables';

export function VariableViewPage() {
  const navigate = useNavigate();
  const { id = '' } = useParams();
  const query = useVariable(id);

  if (query.isLoading) {
    return <LoadingOverlay open />;
  }

  if (query.error) {
    return <Alert severity="error">Failed to load variable details.</Alert>;
  }

  if (!query.data) {
    return <EmptyState title="Variable not found" description="The requested variable does not exist." />;
  }

  const row = query.data;

  return (
    <Stack spacing={3}>
      <PageHeader
        title={row.display_name}
        subtitle="Variable details"
        actions={
          <Button variant="contained" startIcon={<EditOutlinedIcon />} onClick={() => navigate(VARIABLE_ROUTES.edit(row.id))}>
            Edit
          </Button>
        }
      />

      <Paper variant="outlined" sx={{ p: 3 }}>
        <Stack spacing={1}>
          <Typography><strong>Code:</strong> {row.code}</Typography>
          <Typography><strong>Status:</strong> {row.status}</Typography>
          <Typography><strong>Name:</strong> {row.name}</Typography>
          <Typography><strong>Display Name:</strong> {row.display_name}</Typography>
          <Typography><strong>Group ID:</strong> {row.group?.id ?? '-'}</Typography>
          <Typography><strong>Group:</strong> {row.group?.name ?? '-'}</Typography>
          <Typography><strong>Data Type:</strong> {row.data_type}</Typography>
          <Typography><strong>Source Type:</strong> {row.source_type}</Typography>
          <Typography><strong>Source Reference:</strong> {row.source_reference || '-'}</Typography>
          <Typography><strong>Default Value:</strong> {row.default_value || '-'}</Typography>
          <Typography><strong>Required:</strong> {row.is_required ? 'Yes' : 'No'}</Typography>
          <Typography><strong>Description:</strong> {row.description || '-'}</Typography>
        </Stack>
      </Paper>
    </Stack>
  );
}
