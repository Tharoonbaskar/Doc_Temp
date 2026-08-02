import { axiosClient } from '../../../api/axiosClient';
import type { ApiSuccessResponse } from '../../../types/api';
import type { 
  TemplateItem, 
  TemplatePayload, 
  SendForReviewPayload, 
  ApproveTemplatePayload, 
  SendBackPayload,
  VersionChangesResponse,
  TemplateVersionDetailResponse,
  ElementChange,
  ReviewChangePayload,
  ParseWordDocumentResponse,
  TemplatePdfRequestPayload,
  TemplatePdfPreviewResponse,
  TemplatePdfGenerateResponse,
  TemplatePdfVariableResolutionMode,
} from '../types';

const BASE_PATH = '/templates';

export const templatesApi = {
  async list(): Promise<TemplateItem[]> {
    const { data } = await axiosClient.get<ApiSuccessResponse<TemplateItem[]>>(BASE_PATH);
    return data.data ?? [];
  },
  async getById(id: string): Promise<TemplateItem> {
    const { data } = await axiosClient.get<ApiSuccessResponse<TemplateItem>>(`${BASE_PATH}/${id}/`);
    return data.data;
  },
  async create(payload: TemplatePayload): Promise<TemplateItem> {
    const { data} = await axiosClient.post<ApiSuccessResponse<TemplateItem>>(`${BASE_PATH}/`, payload);
    return data.data;
  },
  async update(id: string, payload: TemplatePayload): Promise<TemplateItem> {
    const { data } = await axiosClient.put<ApiSuccessResponse<TemplateItem>>(`${BASE_PATH}/${id}/`, payload);
    return data.data;
  },
  async remove(id: string): Promise<void> {
    await axiosClient.delete(`${BASE_PATH}/${id}/`);
  },
  async sendForReview(id: string, payload: SendForReviewPayload): Promise<TemplateItem> {
    const { data } = await axiosClient.post<ApiSuccessResponse<TemplateItem>>(`${BASE_PATH}/${id}/send-for-review/`, payload);
    return data.data;
  },
  async approve(id: string, payload: ApproveTemplatePayload): Promise<TemplateItem> {
    const { data } = await axiosClient.post<ApiSuccessResponse<TemplateItem>>(`${BASE_PATH}/${id}/approve/`, payload);
    return data.data;
  },
  async sendBack(id: string, payload: SendBackPayload): Promise<TemplateItem> {
    const { data } = await axiosClient.post<ApiSuccessResponse<TemplateItem>>(`${BASE_PATH}/${id}/send-back/`, payload);
    return data.data;
  },
  async parseWordDocument(file: File): Promise<ParseWordDocumentResponse> {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await axiosClient.post<ApiSuccessResponse<ParseWordDocumentResponse>>(
      `${BASE_PATH}/parse-word-document/`,
      formData,
      {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      },
    );
    return data.data;
  },
  async getVersionChanges(templateId: string, versionNumber: number): Promise<VersionChangesResponse> {
    const { data } = await axiosClient.get<ApiSuccessResponse<VersionChangesResponse>>(
      `${BASE_PATH}/${templateId}/versions/${versionNumber}/changes/`
    );
    return data.data;
  },
  async getVersionDetail(templateId: string, versionNumber: number): Promise<TemplateVersionDetailResponse> {
    const { data } = await axiosClient.get<ApiSuccessResponse<TemplateVersionDetailResponse>>(
      `${BASE_PATH}/${templateId}/versions/${versionNumber}/`
    );
    return data.data;
  },
  async updateDraftVersion(
    templateId: string,
    versionNumber: number,
    payload: {
      prosemirror_json: Record<string, unknown>;
      page_size?: 'A4' | 'A3' | 'LETTER' | 'LEGAL';
      page_orientation?: 'PORTRAIT' | 'LANDSCAPE';
    },
  ): Promise<any> {
    const { data } = await axiosClient.put<ApiSuccessResponse<any>>(
      `${BASE_PATH}/${templateId}/versions/${versionNumber}/edit/`,
      payload
    );
    return data.data;
  },
  async sendDraftVersionForReview(templateId: string, versionNumber: number): Promise<any> {
    const { data } = await axiosClient.post<ApiSuccessResponse<any>>(
      `${BASE_PATH}/${templateId}/versions/${versionNumber}/send-for-review/`
    );
    return data.data;
  },
  async approveDraftVersion(templateId: string, versionNumber: number): Promise<any> {
    const { data } = await axiosClient.post<ApiSuccessResponse<any>>(
      `${BASE_PATH}/${templateId}/versions/${versionNumber}/approve/`
    );
    return data.data;
  },
  async deleteDraftVersion(templateId: string, versionNumber: number): Promise<any> {
    const { data } = await axiosClient.delete<ApiSuccessResponse<any>>(
      `${BASE_PATH}/${templateId}/versions/${versionNumber}/discard/`
    );
    return data.data;
  },
  async reviewElementChange(changeId: string, payload: ReviewChangePayload): Promise<ElementChange> {
    const { data } = await axiosClient.post<ApiSuccessResponse<ElementChange>>(
      `${BASE_PATH}/changes/${changeId}/review/`,
      payload
    );
    return data.data;
  },
  async previewPdf(templateId: string, payload: TemplatePdfRequestPayload): Promise<TemplatePdfPreviewResponse> {
    const { data } = await axiosClient.post<ApiSuccessResponse<TemplatePdfPreviewResponse>>(
      `${BASE_PATH}/${templateId}/preview-pdf/`,
      payload,
    );
    return data.data;
  },
  async generatePdf(templateId: string, payload: TemplatePdfRequestPayload): Promise<TemplatePdfGenerateResponse> {
    const { data } = await axiosClient.post<ApiSuccessResponse<TemplatePdfGenerateResponse>>(
      `${BASE_PATH}/${templateId}/generate-pdf/`,
      payload,
    );
    return data.data;
  },
  downloadPdfUrl(
    templateId: string,
    options?: {
      version?: string;
      variables?: Record<string, unknown>;
      variable_resolution_mode?: TemplatePdfVariableResolutionMode;
      watermark?: string;
    },
  ): string {
    const params = new URLSearchParams();
    if (options?.version) {
      params.set('version', options.version);
    }
    if (options?.variables && Object.keys(options.variables).length > 0) {
      params.set('variables', JSON.stringify(options.variables));
    }
    if (options?.variable_resolution_mode) {
      params.set('variable_resolution_mode', options.variable_resolution_mode);
    }
    if (options?.watermark) {
      params.set('watermark', options.watermark);
    }

    const query = params.toString();
    return `${axiosClient.defaults.baseURL}${BASE_PATH}/${templateId}/download-pdf/${query ? `?${query}` : ''}`;
  },
};
