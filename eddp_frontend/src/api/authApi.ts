import { axiosClient } from './axiosClient';
import type { ApiSuccessResponse } from '../types/api';
import type { AuthUser, LoginPayload, LoginResult } from '../types/auth';

export const authApi = {
  async login(payload: LoginPayload): Promise<LoginResult> {
    const { data } = await axiosClient.post<ApiSuccessResponse<LoginResult>>('/auth/login', payload);
    return data.data;
  },
  async logout(refresh: string): Promise<void> {
    await axiosClient.post('/auth/logout', { refresh });
  },
  async profile(): Promise<AuthUser> {
    const { data } = await axiosClient.get<ApiSuccessResponse<AuthUser>>('/auth/profile');
    return data.data;
  },
};
