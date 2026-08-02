import type { ApiSuccessResponse } from '../../types/api';

export type Uuid = string;

export type EntityStatus = 'ACTIVE' | 'INACTIVE' | 'DRAFT' | 'PUBLISHED' | 'ARCHIVED';

export type AuditUser = {
  id?: Uuid;
  username?: string;
  email?: string;
  first_name?: string;
  last_name?: string;
};

export type BaseEntity = {
  id: Uuid;
  code: string;
  status: EntityStatus;
  created_at: string;
  updated_at: string;
  is_deleted: boolean;
  deleted_at: string | null;
  created_by?: AuditUser | null;
  updated_by?: AuditUser | null;
};

export type ListQueryState = {
  search: string;
  status: '' | EntityStatus;
  page: number;
  pageSize: number;
};

export type PaginatedResult<T> = {
  rows: T[];
  total: number;
  page: number;
  pageSize: number;
};

export const DEFAULT_PAGE_SIZE = 10;

export const toApiList = <T>(response: ApiSuccessResponse<T[]>): T[] => response.data ?? [];
