import { axiosClient } from '../../../api/axiosClient';
import type { ApiSuccessResponse } from '../../../types/api';
import type { DocumentItem, DocumentPayload } from '../types';

const BASE_PATH = '/documents';

export const documentsApi = {
  async list(): Promise<DocumentItem[]> {
    const { data } = await axiosClient.get<ApiSuccessResponse<DocumentItem[]>>(BASE_PATH);
    return data.data ?? [];
  },
  async getById(id: string): Promise<DocumentItem> {
    const { data } = await axiosClient.get<ApiSuccessResponse<DocumentItem>>(`${BASE_PATH}/${id}/`);
    return data.data;
  },
  async create(payload: DocumentPayload): Promise<DocumentItem> {
    const { data } = await axiosClient.post<ApiSuccessResponse<DocumentItem>>(`${BASE_PATH}/`, payload);
    return data.data;
  },
  async update(id: string, payload: DocumentPayload): Promise<DocumentItem> {
    const { data } = await axiosClient.put<ApiSuccessResponse<DocumentItem>>(`${BASE_PATH}/${id}/`, payload);
    return data.data;
  },
  async remove(id: string): Promise<void> {
    await axiosClient.delete(`${BASE_PATH}/${id}/`);
  },
};
