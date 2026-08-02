import { axiosClient } from '../../../api/axiosClient';
import type { ApiSuccessResponse } from '../../../types/api';
import type {
  RuntimeDownloadResponse,
  RuntimeGeneratePayload,
  RuntimeGenerateResponse,
  RuntimeGenerationRequestItem,
  RuntimeHistoryResponse,
  RuntimePreviewPayload,
  RuntimePreviewResponse,
  RuntimeStatusResponse,
} from '../types';

const BASE_PATH = '/runtime';
const PREVIEW_PATH = '/document-preview';
const GENERATE_PATH = '/generate';

const normalizeRequestId = (value: string | null | undefined): string => {
  const normalized = (value ?? '').trim();
  if (!normalized) {
    return '';
  }
  const lowered = normalized.toLowerCase();
  if (lowered === 'undefined' || lowered === 'null') {
    return '';
  }
  return normalized;
};

export const runtimeApi = {
  async listGenerationRequests(): Promise<RuntimeGenerationRequestItem[]> {
    const { data } = await axiosClient.get<ApiSuccessResponse<RuntimeGenerationRequestItem[]>>(
      `${BASE_PATH}/generation-requests`,
    );
    return data.data ?? [];
  },

  async preview(payload: RuntimePreviewPayload): Promise<RuntimePreviewResponse> {
    const { data } = await axiosClient.post<ApiSuccessResponse<RuntimePreviewResponse>>(PREVIEW_PATH, payload);
    return data.data;
  },

  async generate(payload: RuntimeGeneratePayload): Promise<RuntimeGenerateResponse> {
    const { data } = await axiosClient.post<ApiSuccessResponse<RuntimeGenerateResponse>>(GENERATE_PATH, payload);
    return data.data;
  },

  async status(requestId: string): Promise<RuntimeStatusResponse> {
    const normalizedRequestId = normalizeRequestId(requestId);
    if (!normalizedRequestId) {
      throw new Error('Request ID is required to fetch runtime status.');
    }

    const { data } = await axiosClient.get<ApiSuccessResponse<RuntimeStatusResponse>>(
      `${BASE_PATH}/status/${encodeURIComponent(normalizedRequestId)}`,
    );
    return data.data;
  },

  async history(correlationId: string): Promise<RuntimeHistoryResponse> {
    const { data } = await axiosClient.get<ApiSuccessResponse<RuntimeHistoryResponse>>(
      `${BASE_PATH}/history/${encodeURIComponent(correlationId)}`,
    );
    return data.data;
  },

  async download(requestId: string): Promise<RuntimeDownloadResponse> {
    const normalizedRequestId = normalizeRequestId(requestId);
    if (!normalizedRequestId) {
      throw new Error('Request ID is required to download runtime output.');
    }

    const { data } = await axiosClient.get<ApiSuccessResponse<RuntimeDownloadResponse>>(
      `${BASE_PATH}/download/${encodeURIComponent(normalizedRequestId)}`,
    );
    return data.data;
  },
};
