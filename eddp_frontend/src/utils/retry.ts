import type { AxiosError } from 'axios';

export const shouldRetry = (error: AxiosError, retryCount: number): boolean => {
  if (retryCount >= 2) {
    return false;
  }

  const status = error.response?.status;
  if (!status) {
    return true;
  }

  return status >= 500;
};

export const waitBeforeRetry = async (retryCount: number): Promise<void> => {
  const delay = (retryCount + 1) * 300;
  await new Promise((resolve) => setTimeout(resolve, delay));
};
