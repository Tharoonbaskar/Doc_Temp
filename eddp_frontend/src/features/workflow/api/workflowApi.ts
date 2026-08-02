import { axiosClient } from '../../../api/axiosClient';
import type { ApiSuccessResponse } from '../../../types/api';
import type { WorkflowItem, WorkflowPayload } from '../types';

const BASE_PATH = '/workflow';

export const workflowApi = {
  async list(): Promise<WorkflowItem[]> {
    const { data } = await axiosClient.get<ApiSuccessResponse<WorkflowItem[]>>(BASE_PATH);
    return data.data ?? [];
  },
  async getById(id: string): Promise<WorkflowItem> {
    const { data } = await axiosClient.get<ApiSuccessResponse<WorkflowItem>>(`${BASE_PATH}/${id}/`);
    return data.data;
  },
  async create(payload: WorkflowPayload): Promise<WorkflowItem> {
    const { data } = await axiosClient.post<ApiSuccessResponse<WorkflowItem>>(`${BASE_PATH}/`, payload);
    return data.data;
  },
  async update(id: string, payload: WorkflowPayload): Promise<WorkflowItem> {
    const { data } = await axiosClient.put<ApiSuccessResponse<WorkflowItem>>(`${BASE_PATH}/${id}/`, payload);
    return data.data;
  },
  async remove(id: string): Promise<void> {
    await axiosClient.delete(`${BASE_PATH}/${id}/`);
  },
};
