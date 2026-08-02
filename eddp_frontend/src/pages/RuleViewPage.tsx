import EditOutlinedIcon from '@mui/icons-material/EditOutlined';
import { Alert, Button, Paper, Stack, Typography } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { LoadingOverlay } from '../components/common/LoadingOverlay';
import { PageHeader } from '../components/common/PageHeader';
import { RULE_ROUTES } from '../constants/appConstants';
import { useRule } from '../features/rules/hooks/useRules';

export function RuleViewPage() {
  const navigate = useNavigate();
  const { id = '' } = useParams();
  const query = useRule(id);

  if (query.isLoading) {
    return <LoadingOverlay open />;
  }

  if (query.error) {
    return <Alert severity="error">Failed to load rule details.</Alert>;
  }

  if (!query.data) {
    return <EmptyState title="Rule not found" description="The requested rule does not exist." />;
  }

  const row = query.data;

  return (
    <Stack spacing={3}>
      <PageHeader
        title={row.name}
        subtitle="Rule details"
        actions={
          <Button variant="contained" startIcon={<EditOutlinedIcon />} onClick={() => navigate(RULE_ROUTES.edit(row.id))}>
            Edit
          </Button>
        }
      />

      <Paper variant="outlined" sx={{ p: 3 }}>
        <Stack spacing={1}>
          <Typography><strong>Code:</strong> {row.code}</Typography>
          <Typography><strong>Status:</strong> {row.status}</Typography>
          <Typography><strong>Rule Group ID:</strong> {row.rule_group?.id ?? '-'}</Typography>
          <Typography><strong>Rule Group:</strong> {row.rule_group?.name ?? '-'}</Typography>
          <Typography><strong>Rule Type:</strong> {row.rule_type}</Typography>
          <Typography><strong>Execution Order:</strong> {row.execution_order}</Typography>
          <Typography><strong>Active:</strong> {row.is_active ? 'Yes' : 'No'}</Typography>
          <Typography><strong>Expression:</strong> {row.expression}</Typography>
          <Typography><strong>Description:</strong> {row.description || '-'}</Typography>
        </Stack>
      </Paper>
    </Stack>
  );
}
