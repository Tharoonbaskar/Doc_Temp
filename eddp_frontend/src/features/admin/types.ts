import type { BaseEntity, EntityStatus, Uuid } from '../shared/types';

export type RoleItem = BaseEntity & {
  name: string;
  description: string;
};

export type RolePayload = {
  code: string;
  name: string;
  description: string;
  status: EntityStatus;
};

export type PermissionItem = BaseEntity & {
  module: string;
  action: string;
  description: string;
};

export type UserItem = {
  id: Uuid;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  is_active: boolean;
  roles: string[];
  permissions: Array<{
    module: string;
    action: string;
  }>;
};

export type ProfilePayload = {
  first_name?: string;
  last_name?: string;
  email?: string;
};

export type ChangePasswordPayload = {
  current_password: string;
  new_password: string;
  confirm_password: string;
};

export type ApplicationSettings = {
  appName: string;
  apiBaseUrl: string;
  apiTimeoutMs: number;
  sessionTimeoutMs: number;
  enableNotifications: boolean;
  dateFormat: string;
};

export type ThemeSettings = {
  mode: 'light' | 'dark';
  primaryColor: string;
  secondaryColor: string;
  density: 'compact' | 'comfortable';
};

export type HealthStatus = {
  status: string;
};
