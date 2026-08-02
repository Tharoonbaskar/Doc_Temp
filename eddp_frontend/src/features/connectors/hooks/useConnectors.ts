import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { connectorsApi } from '../api/connectorsApi';
import type { ConnectorPayload } from '../types';

const KEY = ['connectors'];

export const useConnectors = () =>
  useQuery({
    queryKey: KEY,
    queryFn: connectorsApi.list,
  });

export const useConnector = (id: string) =>
  useQuery({
    queryKey: [...KEY, id],
    queryFn: () => connectorsApi.getById(id),
    enabled: Boolean(id),
  });

export const useCreateConnector = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: ConnectorPayload) => connectorsApi.create(payload),
    onSuccess: () => client.invalidateQueries({ queryKey: KEY }),
  });
};

export const useUpdateConnector = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ConnectorPayload }) => connectorsApi.update(id, payload),
    onSuccess: (_, variables) => {
      client.invalidateQueries({ queryKey: KEY });
      client.invalidateQueries({ queryKey: [...KEY, variables.id] });
    },
  });
};

export const useDeleteConnector = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => connectorsApi.remove(id),
    onSuccess: () => client.invalidateQueries({ queryKey: KEY }),
  });
};
