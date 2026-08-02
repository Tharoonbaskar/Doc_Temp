import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { variablesApi } from '../api/variablesApi';
import type { VariablePayload } from '../types';

const KEY = ['variables'];

export const useVariables = (params?: { document_id?: string }) =>
  useQuery({
    queryKey: params?.document_id ? [...KEY, 'by-document', params.document_id] : KEY,
    queryFn: () => variablesApi.list(params),
  });

export const useVariablesByDocument = (documentId: string | undefined) =>
  useQuery({
    queryKey: [...KEY, 'by-document', documentId || 'none'],
    queryFn: () => variablesApi.list(documentId ? { document_id: documentId } : undefined),
    enabled: Boolean(documentId),
  });

export const useVariable = (id: string) =>
  useQuery({
    queryKey: [...KEY, id],
    queryFn: () => variablesApi.getById(id),
    enabled: Boolean(id),
  });

export const useCreateVariable = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: VariablePayload) => variablesApi.create(payload),
    onSuccess: () => client.invalidateQueries({ queryKey: KEY }),
  });
};

export const useUpdateVariable = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: VariablePayload }) => variablesApi.update(id, payload),
    onSuccess: (_, variables) => {
      client.invalidateQueries({ queryKey: KEY });
      client.invalidateQueries({ queryKey: [...KEY, variables.id] });
    },
  });
};

export const useDeleteVariable = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => variablesApi.remove(id),
    onSuccess: () => client.invalidateQueries({ queryKey: KEY }),
  });
};
