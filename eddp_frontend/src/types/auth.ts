export interface ProgramAccess {
  program_code: string;
  module_name?: string;
  application_name?: string;
}

export interface PermissionAccess {
  module: string;
  action: string;
}

export interface AuthUser {
  id: string;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  is_active: boolean;
  roles: string[];
  permissions: PermissionAccess[];
  programs: ProgramAccess[];
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface LoginPayload {
  username: string;
  password: string;
}

export interface LoginResult {
  tokens: AuthTokens;
  user: AuthUser;
}
