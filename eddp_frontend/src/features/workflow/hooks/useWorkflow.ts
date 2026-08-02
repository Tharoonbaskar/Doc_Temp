import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { workflowApi } from '../api/workflowApi';
import type { WorkflowPayload } from '../types';

const KEY = ['workflow'];

export const useWorkflowList = () =>
  useQuery({
    queryKey: KEY,
    queryFn: workflowApi.list,
  });

export const useWorkflow = (id: string) =>
  useQuery({
    queryKey: [...KEY, id],
    queryFn: () => workflowApi.getById(id),
    enabled: Boolean(id),
  });

export const useCreateWorkflow = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: WorkflowPayload) => workflowApi.create(payload),
    onSuccess: () => client.invalidateQueries({ queryKey: KEY }),
  });
};

export const useUpdateWorkflow = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: WorkflowPayload }) => workflowApi.update(id, payload),
    onSuccess: (_, variables) => {
      client.invalidateQueries({ queryKey: KEY });
      client.invalidateQueries({ queryKey: [...KEY, variables.id] });
    },
  });
};

export const useDeleteWorkflow = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => workflowApi.remove(id),
    onSuccess: () => client.invalidateQueries({ queryKey: KEY }),
  });
};
