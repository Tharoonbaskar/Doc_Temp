import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { templatesApi } from '../api/templatesApi';
import type { 
  TemplatePayload, 
  SendForReviewPayload, 
  ApproveTemplatePayload, 
  SendBackPayload,
  ReviewChangePayload,
  TemplatePdfRequestPayload,
} from '../types';

const KEY = ['templates'];

export const useTemplates = () =>
  useQuery({
    queryKey: KEY,
    queryFn: templatesApi.list,
    staleTime: 0, // Always consider data stale to force refetch
    refetchOnMount: true,
  });

export const useTemplate = (id: string) =>
  useQuery({
    queryKey: [...KEY, id],
    queryFn: () => templatesApi.getById(id),
    enabled: Boolean(id),
    staleTime: 0,
    refetchOnMount: true,
  });

export const useCreateTemplate = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: TemplatePayload) => templatesApi.create(payload),
    onSuccess: () => client.invalidateQueries({ queryKey: KEY }),
  });
};

export const useUpdateTemplate = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: TemplatePayload }) => templatesApi.update(id, payload),
    onSuccess: (_data: unknown, variables: { id: string; payload: TemplatePayload }) => {
      client.invalidateQueries({ queryKey: KEY });
      client.invalidateQueries({ queryKey: [...KEY, variables.id] });
    },
  });
};

export const useDeleteTemplate = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => templatesApi.remove(id),
    onSuccess: () => client.invalidateQueries({ queryKey: KEY }),
  });
};

export const useSendTemplateForReview = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: SendForReviewPayload }) => templatesApi.sendForReview(id, payload),
    onSuccess: (_data: unknown, variables: { id: string; payload: SendForReviewPayload }) => {
      client.invalidateQueries({ queryKey: KEY });
      client.invalidateQueries({ queryKey: [...KEY, variables.id] });
    },
  });
};

export const useApproveTemplate = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: ApproveTemplatePayload }) => templatesApi.approve(id, payload),
    onSuccess: (_data: unknown, variables: { id: string; payload: ApproveTemplatePayload }) => {
      client.invalidateQueries({ queryKey: KEY });
      client.invalidateQueries({ queryKey: [...KEY, variables.id] });
    },
  });
};

export const useSendBackTemplate = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: SendBackPayload }) => templatesApi.sendBack(id, payload),
    onSuccess: (_data: unknown, variables: { id: string; payload: SendBackPayload }) => {
      client.invalidateQueries({ queryKey: KEY });
      client.invalidateQueries({ queryKey: [...KEY, variables.id] });
    },
  });
};

export const useParseWordDocument = () => {
  return useMutation({
    mutationFn: (file: File) => templatesApi.parseWordDocument(file),
  });
};

// Version management hooks
export const useVersionChanges = (templateId: string, versionNumber: number, enabled: boolean = true) =>
  useQuery({
    queryKey: [...KEY, templateId, 'versions', versionNumber, 'changes'],
    queryFn: () => templatesApi.getVersionChanges(templateId, versionNumber),
    enabled: enabled && Boolean(templateId) && versionNumber > 0,
    staleTime: 0,
    refetchOnMount: true,
  });

export const useTemplateVersionDetail = (templateId: string, versionNumber: number, enabled: boolean = true) =>
  useQuery({
    queryKey: [...KEY, templateId, 'versions', versionNumber, 'detail'],
    queryFn: () => templatesApi.getVersionDetail(templateId, versionNumber),
    enabled: enabled && Boolean(templateId) && versionNumber > 0,
    staleTime: 0,
    refetchOnMount: true,
  });

export const useUpdateDraftVersion = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({
      templateId,
      versionNumber,
      prosemirrorJson,
      pageSize,
      pageOrientation,
    }: {
      templateId: string;
      versionNumber: number;
      prosemirrorJson: Record<string, unknown>;
      pageSize?: 'A4' | 'A3' | 'LETTER' | 'LEGAL';
      pageOrientation?: 'PORTRAIT' | 'LANDSCAPE';
    }) =>
      templatesApi.updateDraftVersion(templateId, versionNumber, {
        prosemirror_json: prosemirrorJson,
        page_size: pageSize,
        page_orientation: pageOrientation,
      }),
    onSuccess: (_data, variables) => {
      client.invalidateQueries({ queryKey: KEY });
      client.invalidateQueries({ queryKey: [...KEY, variables.templateId] });
      client.invalidateQueries({ queryKey: [...KEY, variables.templateId, 'versions', variables.versionNumber, 'detail'] });
      client.invalidateQueries({ queryKey: [...KEY, variables.templateId, 'versions', variables.versionNumber, 'changes'] });
    },
  });
};

export const useSendDraftVersionForReview = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ templateId, versionNumber }: { templateId: string; versionNumber: number }) =>
      templatesApi.sendDraftVersionForReview(templateId, versionNumber),
    onSuccess: (_data, variables) => {
      client.invalidateQueries({ queryKey: KEY });
      client.invalidateQueries({ queryKey: [...KEY, variables.templateId] });
      client.invalidateQueries({ queryKey: [...KEY, variables.templateId, 'versions', variables.versionNumber, 'detail'] });
      client.invalidateQueries({ queryKey: [...KEY, variables.templateId, 'versions', variables.versionNumber, 'changes'] });
    },
  });
};

export const useApproveDraftVersion = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ templateId, versionNumber }: { templateId: string; versionNumber: number }) => 
      templatesApi.approveDraftVersion(templateId, versionNumber),
    onSuccess: (_data: unknown, variables: { templateId: string; versionNumber: number }) => {
      // Remove specific template and version queries to force complete refetch
      client.removeQueries({ queryKey: [...KEY, variables.templateId] });
      client.removeQueries({ queryKey: [...KEY, variables.templateId, 'versions', variables.versionNumber, 'detail'] });
      client.removeQueries({ queryKey: [...KEY, variables.templateId, 'versions', variables.versionNumber, 'changes'] });
      // Invalidate list and other version queries
      client.invalidateQueries({ queryKey: KEY });
      client.invalidateQueries({ queryKey: [...KEY, variables.templateId, 'versions'] });
    },
  });
};

export const useDeleteDraftVersion = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ templateId, versionNumber }: { templateId: string; versionNumber: number }) =>
      templatesApi.deleteDraftVersion(templateId, versionNumber),
    onSuccess: (_data, variables) => {
      client.invalidateQueries({ queryKey: KEY });
      client.invalidateQueries({ queryKey: [...KEY, variables.templateId] });
      client.invalidateQueries({ queryKey: [...KEY, variables.templateId, 'versions'] });
    },
  });
};

export const useReviewElementChange = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ changeId, payload }: { changeId: string; payload: ReviewChangePayload }) => 
      templatesApi.reviewElementChange(changeId, payload),
    onSuccess: () => {
      // Invalidate all version changes queries to refresh the UI
      client.invalidateQueries({ queryKey: [...KEY] });
    },
  });
};

export const useTemplatePdfPreview = () =>
  useMutation({
    mutationFn: ({ templateId, payload }: { templateId: string; payload: TemplatePdfRequestPayload }) =>
      templatesApi.previewPdf(templateId, payload),
  });

export const useTemplatePdfGenerate = () =>
  useMutation({
    mutationFn: ({ templateId, payload }: { templateId: string; payload: TemplatePdfRequestPayload }) =>
      templatesApi.generatePdf(templateId, payload),
  });
