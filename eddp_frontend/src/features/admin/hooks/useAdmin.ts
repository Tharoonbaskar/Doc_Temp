import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { adminApi } from '../api/adminApi';
import type {
  ApplicationSettings,
  ChangePasswordPayload,
  ProfilePayload,
  RolePayload,
  ThemeSettings,
} from '../types';

const KEY = ['admin'];

export const useRoles = () =>
  useQuery({
    queryKey: [...KEY, 'roles'],
    queryFn: adminApi.listRoles,
  });

export const useRole = (id: string) =>
  useQuery({
    queryKey: [...KEY, 'roles', id],
    queryFn: () => adminApi.getRole(id),
    enabled: Boolean(id),
  });

export const useCreateRole = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: RolePayload) => adminApi.createRole(payload),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: [...KEY, 'roles'] });
    },
  });
};

export const useUpdateRole = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: RolePayload }) => adminApi.updateRole(id, payload),
    onSuccess: (_, variables) => {
      client.invalidateQueries({ queryKey: [...KEY, 'roles'] });
      client.invalidateQueries({ queryKey: [...KEY, 'roles', variables.id] });
    },
  });
};

export const useDeleteRole = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => adminApi.removeRole(id),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: [...KEY, 'roles'] });
    },
  });
};

export const usePermissions = () =>
  useQuery({
    queryKey: [...KEY, 'permissions'],
    queryFn: adminApi.listPermissions,
  });

export const useUsers = () =>
  useQuery({
    queryKey: [...KEY, 'users'],
    queryFn: adminApi.listUsers,
  });

export const useProfile = () =>
  useQuery({
    queryKey: [...KEY, 'profile'],
    queryFn: adminApi.profile,
  });

export const useUpdateProfile = () => {
  const client = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProfilePayload) => adminApi.updateProfile(payload),
    onSuccess: () => {
      client.invalidateQueries({ queryKey: [...KEY, 'profile'] });
    },
  });
};

export const useChangePassword = () =>
  useMutation({
    mutationFn: (payload: ChangePasswordPayload) => adminApi.changePassword(payload),
  });

export const useApplicationSettings = () =>
  useQuery({
    queryKey: [...KEY, 'application-settings'],
    queryFn: adminApi.getApplicationSettings,
  });

export const useSaveApplicationSettings = () =>
  useMutation({
    mutationFn: (payload: ApplicationSettings) => adminApi.saveApplicationSettings(payload),
  });

export const useThemeSettings = (mode: 'light' | 'dark') =>
  useQuery({
    queryKey: [...KEY, 'theme-settings', mode],
    queryFn: () => adminApi.getThemeSettings(mode),
  });

export const useSaveThemeSettings = () =>
  useMutation({
    mutationFn: (payload: ThemeSettings) => adminApi.saveThemeSettings(payload),
  });

export const useSystemHealth = () =>
  useQuery({
    queryKey: [...KEY, 'system-health'],
    queryFn: adminApi.health,
    refetchInterval: 30000,
  });
