import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { runtimeApi } from '../api/runtimeApi';
import type { RuntimeGeneratePayload, RuntimePreviewPayload } from '../types';

const KEY = ['runtime'];
const REQUESTS_KEY = [...KEY, 'generation-requests'];

export const useRuntimeGenerationRequests = () =>
  useQuery({
    queryKey: REQUESTS_KEY,
    queryFn: runtimeApi.listGenerationRequests,
  });

export const useRuntimeStatus = (requestId: string) =>
  useQuery({
    queryKey: [...KEY, 'status', requestId],
    queryFn: () => runtimeApi.status(requestId),
    enabled: Boolean(requestId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === 'ACTIVE' ? 3000 : false;
    },
  });

export const useRuntimeHistory = (correlationId: string) =>
  useQuery({
    queryKey: [...KEY, 'history', correlationId],
    queryFn: () => runtimeApi.history(correlationId),
    enabled: Boolean(correlationId),
  });

export const useRuntimePreview = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: RuntimePreviewPayload) => runtimeApi.preview(payload),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: REQUESTS_KEY });
    },
  });
};

export const useRuntimeGenerate = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: RuntimeGeneratePayload) => runtimeApi.generate(payload),
    onSuccess: (response) => {
      client.invalidateQueries({ queryKey: REQUESTS_KEY });
      if (response.request_id) {
        client.invalidateQueries({ queryKey: [...KEY, 'status', response.request_id] });
      }
    },
  });
};

export const useRuntimeDownload = () =>
  useMutation({
    mutationFn: (requestId: string) => runtimeApi.download(requestId),
  });
