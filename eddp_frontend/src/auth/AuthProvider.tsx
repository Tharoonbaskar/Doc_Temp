import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';

import { authApi } from '../api/authApi';
import { SESSION_TIMEOUT_MS } from '../constants/appConstants';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import { AuthContext, type AuthContextValue } from './authContext';
import {
  clearSession as clearSessionAction,
  finishInitialization,
  setSession as setSessionAction,
} from '../store/slices/authSlice';
import type { LoginPayload } from '../types/auth';
import { tokenStorage } from '../utils/tokenStorage';

type Props = {
  children: ReactNode;
};

export function AuthProvider({ children }: Props) {
  const dispatch = useAppDispatch();
  const { user, isAuthenticated, isInitializing, tokens } = useAppSelector((state) => state.auth);
  const [lastActivity, setLastActivity] = useState<number>(() => Date.now());
  const idleIntervalRef = useRef<number | null>(null);

  const clearSession = useCallback(async (): Promise<void> => {
    const refresh = tokenStorage.getRefreshToken();
    if (refresh) {
      try {
        await authApi.logout(refresh);
      } catch {
        // Ignore server-side logout failures during client cleanup.
      }
    }

    tokenStorage.clearSession();
    dispatch(clearSessionAction());
  }, [dispatch]);

  const bootstrap = useCallback(async (): Promise<void> => {
    const access = tokenStorage.getAccessToken();
    const refresh = tokenStorage.getRefreshToken();
    const storedUser = tokenStorage.getUser();

    if (!access || !refresh || !storedUser) {
      dispatch(finishInitialization());
      return;
    }

    try {
      const profile = await authApi.profile();
      tokenStorage.setSession({ access, refresh }, profile);
      dispatch(
        setSessionAction({
          user: profile,
          tokens: { access, refresh },
        }),
      );
    } catch {
      tokenStorage.clearSession();
      dispatch(clearSessionAction());
    } finally {
      dispatch(finishInitialization());
    }
  }, [dispatch]);

  useEffect(() => {
    void bootstrap();
  }, [bootstrap]);

  useEffect(() => {
    const events = ['click', 'mousemove', 'keydown', 'scroll', 'touchstart'];
    const updateActivity = () => setLastActivity(Date.now());

    events.forEach((eventName) => window.addEventListener(eventName, updateActivity));

    return () => {
      events.forEach((eventName) => window.removeEventListener(eventName, updateActivity));
    };
  }, []);

  useEffect(() => {
    if (!isAuthenticated || !tokens) {
      if (idleIntervalRef.current) {
        window.clearInterval(idleIntervalRef.current);
        idleIntervalRef.current = null;
      }
      return;
    }

    idleIntervalRef.current = window.setInterval(() => {
      const idleTime = Date.now() - lastActivity;
      if (idleTime >= SESSION_TIMEOUT_MS) {
        void clearSession();
      }
    }, 30_000);

    return () => {
      if (idleIntervalRef.current) {
        window.clearInterval(idleIntervalRef.current);
        idleIntervalRef.current = null;
      }
    };
  }, [isAuthenticated, tokens, lastActivity, clearSession]);

  const login = useCallback(async (payload: LoginPayload): Promise<void> => {
    const result = await authApi.login(payload);
    tokenStorage.setSession(result.tokens, result.user);
    dispatch(setSessionAction({ user: result.user, tokens: result.tokens }));
  }, [dispatch]);

  const logout = useCallback(async (): Promise<void> => {
    await clearSession();
  }, [clearSession]);

  const hasRole = useCallback((role: string): boolean => {
    const roleName = role.toLowerCase();
    return Boolean(user?.roles.some((item) => item.toLowerCase() === roleName));
  }, [user]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated,
      isInitializing,
      login,
      logout,
      hasRole,
    }),
    [user, isAuthenticated, isInitializing, login, logout, hasRole],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}