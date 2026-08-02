import type { AxiosError } from 'axios';

type ApiErrorShape = {
  message?: string;
  errors?: unknown;
};

const flattenErrorMessages = (value: unknown, prefix = ''): string[] => {
  if (typeof value === 'string') {
    const message = value.trim();
    if (!message) {
      return [];
    }
    return prefix ? [`${prefix}: ${message}`] : [message];
  }

  if (Array.isArray(value)) {
    return value.flatMap((item) => flattenErrorMessages(item, prefix));
  }

  if (value && typeof value === 'object') {
    const entries = Object.entries(value as Record<string, unknown>);
    return entries.flatMap(([key, nested]) => {
      const nextPrefix = key === 'non_field_errors' ? '' : key;
      return flattenErrorMessages(nested, nextPrefix);
    });
  }

  return [];
};

export const getApiErrorMessage = (error: unknown, fallback: string): string => {
  const axiosError = error as AxiosError<ApiErrorShape> | undefined;
  const payload = axiosError?.response?.data;

  const detailedMessages = flattenErrorMessages(payload?.errors);
  if (detailedMessages.length > 0) {
    return detailedMessages[0];
  }

  if (typeof payload?.message === 'string' && payload.message.trim()) {
    return payload.message;
  }

  return fallback;
};
