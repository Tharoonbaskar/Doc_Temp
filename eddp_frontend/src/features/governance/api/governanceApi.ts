import { axiosClient } from '../../../api/axiosClient';
import type { ApiSuccessResponse } from '../../../types/api';
import type { ActivityLogItem, AuditLogItem, SnapshotItem } from '../types';

const BASE_PATH = '/governance';

const readArrayData = <T>(payload: unknown): T[] => {
  if (Array.isArray(payload)) {
    return payload;
  }
  if (payload && typeof payload === 'object') {
    const maybeRows = (payload as { rows?: unknown }).rows;
    if (Array.isArray(maybeRows)) {
      return maybeRows as T[];
    }
  }
  return [];
};

export const governanceApi = {
  async listAuditLogs(): Promise<AuditLogItem[]> {
    const { data } = await axiosClient.get<ApiSuccessResponse<AuditLogItem[]>>(`${BASE_PATH}/audit-logs/`);
    return readArrayData<AuditLogItem>(data.data);
  },

  async getAuditLogById(id: string): Promise<AuditLogItem> {
    const { data } = await axiosClient.get<ApiSuccessResponse<AuditLogItem>>(`${BASE_PATH}/audit-logs/${id}/`);
    return data.data;
  },

  async listActivityLogs(): Promise<ActivityLogItem[]> {
    try {
      const { data } = await axiosClient.get<ApiSuccessResponse<ActivityLogItem[]>>(`${BASE_PATH}/activity-logs/`);
      return readArrayData<ActivityLogItem>(data.data);
    } catch {
      return [];
    }
  },

  async listSnapshots(): Promise<SnapshotItem[]> {
    try {
      const { data } = await axiosClient.get<ApiSuccessResponse<SnapshotItem[]>>(`${BASE_PATH}/snapshots/`);
      return readArrayData<SnapshotItem>(data.data);
    } catch {
      return [];
    }
  },
};
