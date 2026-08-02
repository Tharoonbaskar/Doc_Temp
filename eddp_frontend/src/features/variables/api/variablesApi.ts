import { axiosClient } from '../../../api/axiosClient';
import type { ApiSuccessResponse } from '../../../types/api';
import type { VariableItem, VariablePayload } from '../types';

const BASE_PATH = '/variables';

export const variablesApi = {
  async list(params?: { document_id?: string }): Promise<VariableItem[]> {
    const { data} = await axiosClient.get<ApiSuccessResponse<VariableItem[]>>(BASE_PATH, { params });
    return data.data ?? [];
  },
  async getById(id: string): Promise<VariableItem> {
    const { data } = await axiosClient.get<ApiSuccessResponse<VariableItem>>(`${BASE_PATH}/${id}/`);
    return data.data;
  },
  async create(payload: VariablePayload): Promise<VariableItem> {
    const { data } = await axiosClient.post<ApiSuccessResponse<VariableItem>>(`${BASE_PATH}/`, payload);
    return data.data;
  },
  async update(id: string, payload: VariablePayload): Promise<VariableItem> {
    const { data } = await axiosClient.put<ApiSuccessResponse<VariableItem>>(`${BASE_PATH}/${id}/`, payload);
    return data.data;
  },
  async remove(id: string): Promise<void> {
    await axiosClient.delete(`${BASE_PATH}/${id}/`);
  },
};
