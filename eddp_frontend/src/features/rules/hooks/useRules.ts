import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { rulesApi } from '../api/rulesApi';
import type { RulePayload } from '../types';

const KEY = ['rules'];

export const useRules = () =>
  useQuery({
    queryKey: KEY,
    queryFn: rulesApi.list,
  });

export const useRule = (id: string) =>
  useQuery({
    queryKey: [...KEY, id],
    queryFn: () => rulesApi.getById(id),
    enabled: Boolean(id),
  });

export const useCreateRule = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: RulePayload) => rulesApi.create(payload),
    onSuccess: () => client.invalidateQueries({ queryKey: KEY }),
  });
};

export const useUpdateRule = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: RulePayload }) => rulesApi.update(id, payload),
    onSuccess: (_, variables) => {
      client.invalidateQueries({ queryKey: KEY });
      client.invalidateQueries({ queryKey: [...KEY, variables.id] });
    },
  });
};

export const useDeleteRule = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => rulesApi.remove(id),
    onSuccess: () => client.invalidateQueries({ queryKey: KEY }),
  });
};
