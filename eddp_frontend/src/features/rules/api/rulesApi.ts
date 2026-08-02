import { axiosClient } from '../../../api/axiosClient';
import type { ApiSuccessResponse } from '../../../types/api';
import type { RuleItem, RulePayload } from '../types';

const BASE_PATH = '/generation-rules';

export const rulesApi = {
  async list(): Promise<RuleItem[]> {
    const { data } = await axiosClient.get<ApiSuccessResponse<RuleItem[]>>(BASE_PATH);
    return data.data ?? [];
  },
  async getById(id: string): Promise<RuleItem> {
    const { data } = await axiosClient.get<ApiSuccessResponse<RuleItem>>(`${BASE_PATH}/${id}/`);
    return data.data;
  },
  async create(payload: RulePayload): Promise<RuleItem> {
    const { data } = await axiosClient.post<ApiSuccessResponse<RuleItem>>(`${BASE_PATH}/`, payload);
    return data.data;
  },
  async update(id: string, payload: RulePayload): Promise<RuleItem> {
    const { data } = await axiosClient.put<ApiSuccessResponse<RuleItem>>(`${BASE_PATH}/${id}/`, payload);
    return data.data;
  },
  async remove(id: string): Promise<void> {
    await axiosClient.delete(`${BASE_PATH}/${id}/`);
  },
};
