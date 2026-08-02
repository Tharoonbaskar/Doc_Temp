import { useMemo } from 'react';
import { QueryClientProvider } from '@tanstack/react-query';
import { CssBaseline, ThemeProvider } from '@mui/material';
import { Provider } from 'react-redux';

import App from './App';
import { AuthProvider } from './auth/AuthProvider';
import { queryClient } from './config/queryClient';
import { useAppSelector } from './hooks/reduxHooks';
import { store } from './store';
import { selectThemeMode } from './store/slices/themeSlice';
import { buildTheme } from './theme';

function ThemeBoundApp() {
  const mode = useAppSelector(selectThemeMode);
  const theme = useMemo(() => buildTheme(mode), [mode]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <AuthProvider>
        <App />
      </AuthProvider>
    </ThemeProvider>
  );
}

export default function AppProviders() {
  return (
    <Provider store={store}>
      <QueryClientProvider client={queryClient}>
        <ThemeBoundApp />
      </QueryClientProvider>
    </Provider>
  );
}
