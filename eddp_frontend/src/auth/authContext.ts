import { createContext } from 'react';

import type { LoginPayload } from '../types/auth';
import type { AuthUser } from '../types/auth';

export type AuthContextValue = {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isInitializing: boolean;
  login: (payload: LoginPayload) => Promise<void>;
  logout: () => Promise<void>;
  hasRole: (role: string) => boolean;
};

export const AuthContext = createContext<AuthContextValue | null>(null);
