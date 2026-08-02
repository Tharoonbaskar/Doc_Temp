import { TOKEN_STORAGE_KEYS } from '../constants/appConstants';
import type { AuthTokens, AuthUser } from '../types/auth';

const safeParse = <T>(value: string | null): T | null => {
  if (!value) {
    return null;
  }
  try {
    return JSON.parse(value) as T;
  } catch {
    return null;
  }
};

export const tokenStorage = {
  getAccessToken(): string | null {
    return localStorage.getItem(TOKEN_STORAGE_KEYS.ACCESS);
  },
  getRefreshToken(): string | null {
    return localStorage.getItem(TOKEN_STORAGE_KEYS.REFRESH);
  },
  getUser(): AuthUser | null {
    return safeParse<AuthUser>(localStorage.getItem(TOKEN_STORAGE_KEYS.USER));
  },
  setSession(tokens: AuthTokens, user: AuthUser): void {
    localStorage.setItem(TOKEN_STORAGE_KEYS.ACCESS, tokens.access);
    localStorage.setItem(TOKEN_STORAGE_KEYS.REFRESH, tokens.refresh);
    localStorage.setItem(TOKEN_STORAGE_KEYS.USER, JSON.stringify(user));
  },
  clearSession(): void {
    localStorage.removeItem(TOKEN_STORAGE_KEYS.ACCESS);
    localStorage.removeItem(TOKEN_STORAGE_KEYS.REFRESH);
    localStorage.removeItem(TOKEN_STORAGE_KEYS.USER);
  },
};
