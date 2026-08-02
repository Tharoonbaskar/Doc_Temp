import { axiosClient } from '../../../api/axiosClient';
import type { ApiSuccessResponse } from '../../../types/api';
import type { ConnectorItem, ConnectorPayload } from '../types';

const BASE_PATH = '/connectors';

export const connectorsApi = {
  async list(): Promise<ConnectorItem[]> {
    const { data } = await axiosClient.get<ApiSuccessResponse<ConnectorItem[]>>(BASE_PATH);
    return data.data ?? [];
  },
  async getById(id: string): Promise<ConnectorItem> {
    const { data } = await axiosClient.get<ApiSuccessResponse<ConnectorItem>>(`${BASE_PATH}/${id}/`);
    return data.data;
  },
  async create(payload: ConnectorPayload): Promise<ConnectorItem> {
    const { data } = await axiosClient.post<ApiSuccessResponse<ConnectorItem>>(`${BASE_PATH}/`, payload);
    return data.data;
  },
  async update(id: string, payload: ConnectorPayload): Promise<ConnectorItem> {
    const { data } = await axiosClient.put<ApiSuccessResponse<ConnectorItem>>(`${BASE_PATH}/${id}/`, payload);
    return data.data;
  },
  async remove(id: string): Promise<void> {
    await axiosClient.delete(`${BASE_PATH}/${id}/`);
  },
};
