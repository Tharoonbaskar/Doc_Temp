import { API_TIMEOUT_MS } from '../constants/appConstants';

export const env = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api',
  apiTimeoutMs: Number(import.meta.env.VITE_API_TIMEOUT_MS ?? API_TIMEOUT_MS),
};
