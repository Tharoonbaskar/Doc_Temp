import { Navigate, useLocation } from 'react-router-dom';
import { Box, CircularProgress } from '@mui/material';
import type { ReactNode } from 'react';

import { ROUTES } from '../constants/appConstants';
import { useAuth } from './useAuth';

type Props = {
  children: ReactNode;
  requiredRoles?: readonly string[];
};

export function ProtectedRoute({ children, requiredRoles }: Props) {
  const { isAuthenticated, isInitializing, user } = useAuth();
  const location = useLocation();

  if (isInitializing) {
    return (
      <Box sx={{ minHeight: '100vh', display: 'grid', placeItems: 'center' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} replace state={{ from: location }} />;
  }

  if (requiredRoles && requiredRoles.length > 0) {
    const roleSet = new Set((user?.roles ?? []).map((item) => item.toLowerCase()));
    const hasAnyRole = requiredRoles.some((role) => roleSet.has(role.toLowerCase()));
    if (!hasAnyRole) {
      return <Navigate to={ROUTES.UNAUTHORIZED} replace />;
    }
  }

  return <>{children}</>;
}
