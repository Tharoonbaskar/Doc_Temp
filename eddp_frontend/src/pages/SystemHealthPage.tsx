import CheckCircleOutlinedIcon from '@mui/icons-material/CheckCircleOutlined';
import ErrorOutlineOutlinedIcon from '@mui/icons-material/ErrorOutlineOutlined';
import RefreshOutlinedIcon from '@mui/icons-material/RefreshOutlined';
import {
  Alert,
  Button,
  Chip,
  LinearProgress,
  Paper,
  Stack,
  Typography,
} from '@mui/material';

import { PageHeader } from '../components/common/PageHeader';
import { useSystemHealth } from '../features/admin/hooks/useAdmin';

export function SystemHealthPage() {
  const query = useSystemHealth();
  const status = query.data?.status ?? 'unknown';
  const isHealthy = status.toLowerCase() === 'ok';

  return (
    <Stack spacing={3}>
      <PageHeader title="System Health" subtitle="Service availability, runtime health, and readiness indicators." />

      {query.error ? <Alert severity="error">Health endpoint check failed.</Alert> : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack spacing={2}>
          <Stack direction="row" spacing={1} alignItems="center">
            <Typography variant="subtitle1">Overall Status</Typography>
            <Chip
              label={status.toUpperCase()}
              color={isHealthy ? 'success' : 'error'}
              icon={isHealthy ? <CheckCircleOutlinedIcon /> : <ErrorOutlineOutlinedIcon />}
            />
          </Stack>

          <LinearProgress variant={query.isFetching ? 'indeterminate' : 'determinate'} value={isHealthy ? 100 : 30} sx={{ height: 8, borderRadius: 999 }} />

          <Typography variant="body2" color="text.secondary">
            Last probe source: /api/common/health/
          </Typography>

          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={<RefreshOutlinedIcon />}
              onClick={() => query.refetch()}
              disabled={query.isFetching}
            >
              Refresh
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Stack>
  );
}
