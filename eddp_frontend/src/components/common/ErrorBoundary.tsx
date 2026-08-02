import { type ReactNode } from 'react';
import { Alert, AlertTitle, Box, Button, Container, Typography } from '@mui/material';
import { ErrorBoundary } from 'react-error-boundary';

type Props = {
  children: ReactNode;
};

type FallbackProps = {
  error: Error;
};

function ErrorFallback({ error }: FallbackProps) {
  const handleRefresh = (): void => {
    window.location.reload();
  };

  return (
    <Container maxWidth="sm" sx={{ py: 8 }}>
      <Alert severity="error">
        <AlertTitle>Unexpected Error</AlertTitle>
        <Typography variant="body2">{error.message || 'Something went wrong.'}</Typography>
      </Alert>
      <Box sx={{ mt: 3 }}>
        <Button variant="contained" onClick={handleRefresh}>
          Reload Application
        </Button>
      </Box>
    </Container>
  );
}

export function AppErrorBoundary({ children }: Props) {
  const logError = (error: Error): void => {
    console.error('Application error boundary caught an error:', error);
  };

  return (
    <ErrorBoundary FallbackComponent={ErrorFallback} onError={logError}>
      {children}
    </ErrorBoundary>
  );
}
