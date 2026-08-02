import { axiosClient } from '../../../api/axiosClient';
import { env } from '../../../config/env';
import { APP_NAME, SESSION_TIMEOUT_MS } from '../../../constants/appConstants';
import type { ApiSuccessResponse } from '../../../types/api';
import type {
  ApplicationSettings,
  ChangePasswordPayload,
  HealthStatus,
  PermissionItem,
  ProfilePayload,
  RoleItem,
  RolePayload,
  ThemeSettings,
  UserItem,
} from '../types';

const IDENTITY_BASE = '/identity';
const AUTH_BASE = '/auth';
const COMMON_BASE = '/common';

export const adminApi = {
  async listRoles(): Promise<RoleItem[]> {
    const { data } = await axiosClient.get<ApiSuccessResponse<RoleItem[]>>(`${IDENTITY_BASE}/roles`);
    return data.data ?? [];
  },

  async getRole(id: string): Promise<RoleItem> {
    const { data } = await axiosClient.get<ApiSuccessResponse<RoleItem>>(`${IDENTITY_BASE}/roles/${id}/`);
    return data.data;
  },

  async createRole(payload: RolePayload): Promise<RoleItem> {
    const { data } = await axiosClient.post<ApiSuccessResponse<RoleItem>>(`${IDENTITY_BASE}/roles/`, payload);
    return data.data;
  },

  async updateRole(id: string, payload: RolePayload): Promise<RoleItem> {
    const { data } = await axiosClient.put<ApiSuccessResponse<RoleItem>>(`${IDENTITY_BASE}/roles/${id}/`, payload);
    return data.data;
  },

  async removeRole(id: string): Promise<void> {
    await axiosClient.delete(`${IDENTITY_BASE}/roles/${id}/`);
  },

  async profile(): Promise<UserItem> {
    const { data } = await axiosClient.get<ApiSuccessResponse<UserItem>>(`${AUTH_BASE}/profile`);
    return data.data;
  },

  async updateProfile(payload: ProfilePayload): Promise<UserItem> {
    const { data } = await axiosClient.put<ApiSuccessResponse<UserItem>>(`${AUTH_BASE}/profile`, payload);
    return data.data;
  },

  async changePassword(payload: ChangePasswordPayload): Promise<{ changed: boolean }> {
    const { data } = await axiosClient.post<ApiSuccessResponse<{ changed: boolean }>>(`${AUTH_BASE}/change-password`, payload);
    return data.data;
  },

  async health(): Promise<HealthStatus> {
    const { data } = await axiosClient.get<ApiSuccessResponse<HealthStatus>>(`${COMMON_BASE}/health/`);
    return data.data;
  },

  async listPermissions(): Promise<PermissionItem[]> {
    try {
      const { data } = await axiosClient.get<ApiSuccessResponse<PermissionItem[]>>(`${IDENTITY_BASE}/permissions/`);
      return data.data ?? [];
    } catch {
      return [];
    }
  },

  async listUsers(): Promise<UserItem[]> {
    try {
      const { data } = await axiosClient.get<ApiSuccessResponse<UserItem[]>>(`${IDENTITY_BASE}/users/`);
      return data.data ?? [];
    } catch {
      return [];
    }
  },

  async getApplicationSettings(): Promise<ApplicationSettings> {
    return {
      appName: APP_NAME,
      apiBaseUrl: env.apiBaseUrl,
      apiTimeoutMs: env.apiTimeoutMs,
      sessionTimeoutMs: SESSION_TIMEOUT_MS,
      enableNotifications: true,
      dateFormat: 'YYYY-MM-DD HH:mm:ss',
    };
  },

  async saveApplicationSettings(payload: ApplicationSettings): Promise<ApplicationSettings> {
    return payload;
  },

  async getThemeSettings(mode: 'light' | 'dark'): Promise<ThemeSettings> {
    return {
      mode,
      primaryColor: '#0057A8',
      secondaryColor: '#0C8B5F',
      density: 'comfortable',
    };
  },

  async saveThemeSettings(payload: ThemeSettings): Promise<ThemeSettings> {
    return payload;
  },
};
