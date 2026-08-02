import BlockOutlinedIcon from '@mui/icons-material/BlockOutlined';
import { Button, Container, Stack } from '@mui/material';
import { useNavigate } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { ROUTES } from '../constants/appConstants';

export function UnauthorizedPage() {
  const navigate = useNavigate();

  return (
    <Container maxWidth="sm" sx={{ py: 10 }}>
      <Stack spacing={3}>
        <EmptyState
          icon={<BlockOutlinedIcon color="warning" fontSize="large" />}
          title="Unauthorized"
          description="You do not have access to this page."
        />
        <Button variant="contained" onClick={() => navigate(ROUTES.DASHBOARD)}>
          Go to Dashboard
        </Button>
      </Stack>
    </Container>
  );
}
