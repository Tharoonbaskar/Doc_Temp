import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';

import { env } from '../config/env';
import { TOKEN_STORAGE_KEYS } from '../constants/appConstants';
import { tokenStorage } from '../utils/tokenStorage';
import { waitBeforeRetry, shouldRetry } from '../utils/retry';

const client = axios.create({
  baseURL: env.apiBaseUrl,
  timeout: env.apiTimeoutMs,
  headers: {
    'Content-Type': 'application/json',
  },
});

let refreshInFlight: Promise<string | null> | null = null;

const withAuthHeader = (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
  const accessToken = tokenStorage.getAccessToken();
  if (accessToken) {
    config.headers.set('Authorization', `Bearer ${accessToken}`);
  }
  return config;
};

const refreshAccessToken = async (): Promise<string | null> => {
  const refreshToken = tokenStorage.getRefreshToken();
  if (!refreshToken) {
    return null;
  }

  try {
    const response = await axios.post(`${env.apiBaseUrl}/auth/refresh`, { refresh: refreshToken });
    const access = response.data?.data?.access as string | undefined;
    const refresh = (response.data?.data?.refresh as string | undefined) ?? refreshToken;

    if (!access) {
      return null;
    }

    localStorage.setItem(TOKEN_STORAGE_KEYS.ACCESS, access);
    localStorage.setItem(TOKEN_STORAGE_KEYS.REFRESH, refresh);
    return access;
  } catch {
    return null;
  }
};

client.interceptors.request.use((config) => withAuthHeader(config));

client.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as (InternalAxiosRequestConfig & { _retryCount?: number; _retryAuth?: boolean }) | undefined;
    if (!original) {
      return Promise.reject(error);
    }

    const statusCode = error.response?.status;

    if (statusCode === 401 && !original._retryAuth) {
      original._retryAuth = true;

      if (!refreshInFlight) {
        refreshInFlight = refreshAccessToken().finally(() => {
          refreshInFlight = null;
        });
      }

      const newAccess = await refreshInFlight;
      if (newAccess) {
        original.headers.set('Authorization', `Bearer ${newAccess}`);
        return client(original);
      }

      tokenStorage.clearSession();
      if (window.location.pathname !== '/login') {
        window.location.assign('/login');
      }
      return Promise.reject(error);
    }

    const retryCount = original._retryCount ?? 0;
    if (shouldRetry(error, retryCount)) {
      original._retryCount = retryCount + 1;
      await waitBeforeRetry(retryCount);
      return client(original);
    }

    return Promise.reject(error);
  },
);

export { client as axiosClient };
