import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { documentsApi } from '../api/documentsApi';
import type { DocumentPayload } from '../types';

const KEY = ['documents'];

export const useDocuments = () =>
  useQuery({
    queryKey: KEY,
    queryFn: documentsApi.list,
  });

export const useDocument = (id: string) =>
  useQuery({
    queryKey: [...KEY, id],
    queryFn: () => documentsApi.getById(id),
    enabled: Boolean(id),
  });

export const useCreateDocument = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: DocumentPayload) => documentsApi.create(payload),
    onSuccess: () => client.invalidateQueries({ queryKey: KEY }),
  });
};

export const useUpdateDocument = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: DocumentPayload }) => documentsApi.update(id, payload),
    onSuccess: (_, variables) => {
      client.invalidateQueries({ queryKey: KEY });
      client.invalidateQueries({ queryKey: [...KEY, variables.id] });
    },
  });
};

export const useDeleteDocument = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => documentsApi.remove(id),
    onSuccess: () => client.invalidateQueries({ queryKey: KEY }),
  });
};
