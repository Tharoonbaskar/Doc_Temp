import ErrorOutlineOutlinedIcon from '@mui/icons-material/ErrorOutlineOutlined';
import { Button, Container, Stack } from '@mui/material';
import { useNavigate } from 'react-router-dom';

import { EmptyState } from '../components/common/EmptyState';
import { ROUTES } from '../constants/appConstants';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <Container maxWidth="sm" sx={{ py: 10 }}>
      <Stack spacing={3}>
        <EmptyState
          icon={<ErrorOutlineOutlinedIcon color="error" fontSize="large" />}
          title="Page Not Found"
          description="The page you requested does not exist."
        />
        <Button variant="contained" onClick={() => navigate(ROUTES.DASHBOARD)}>
          Back to Dashboard
        </Button>
      </Stack>
    </Container>
  );
}
