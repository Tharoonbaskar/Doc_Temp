import { zodResolver } from '@hookform/resolvers/zod';
import LoginOutlinedIcon from '@mui/icons-material/LoginOutlined';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { useLocation, useNavigate } from 'react-router-dom';
import { z } from 'zod';

import { useAuth } from '../auth/useAuth';
import { ROUTES } from '../constants/appConstants';

const loginSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [error, setError] = useState<string>('');

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      username: '',
      password: '',
    },
  });

  const onSubmit = async (values: LoginFormValues): Promise<void> => {
    try {
      setError('');
      await login(values);
      const nextPath = (location.state as { from?: { pathname?: string } } | null)?.from?.pathname;
      navigate(nextPath ?? ROUTES.DASHBOARD, { replace: true });
    } catch {
      setError('Login failed. Please verify your credentials.');
    }
  };

  return (
    <Container maxWidth="sm" sx={{ py: 10 }}>
      <Card variant="outlined">
        <CardContent>
          <Stack spacing={3}>
            <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
              <LoginOutlinedIcon color="primary" />
              <Typography variant="h5" sx={{ fontWeight: 700 }}>
                Sign in to EDDP
              </Typography>
            </Stack>

            {error ? <Alert severity="error">{error}</Alert> : null}

            <Box component="form" onSubmit={handleSubmit(onSubmit)} noValidate>
              <Stack spacing={2}>
                <TextField
                  label="Username"
                  {...register('username')}
                  error={Boolean(errors.username)}
                  helperText={errors.username?.message}
                />
                <TextField
                  type="password"
                  label="Password"
                  {...register('password')}
                  error={Boolean(errors.password)}
                  helperText={errors.password?.message}
                />
                <Button type="submit" variant="contained" disabled={isSubmitting}>
                  {isSubmitting ? 'Signing in...' : 'Sign in'}
                </Button>
              </Stack>
            </Box>
          </Stack>
        </CardContent>
      </Card>
    </Container>
  );
}
