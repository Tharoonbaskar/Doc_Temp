import type { BaseEntity, Uuid } from '../shared/types';

export type AuditLogItem = BaseEntity & {
  entity_name: string;
  entity_id: string;
  action: string;
  old_value: Record<string, unknown>;
  new_value: Record<string, unknown>;
  performed_by?: {
    id?: Uuid;
    username?: string;
    email?: string;
    first_name?: string;
    last_name?: string;
  } | null;
  ip_address: string | null;
  user_agent: string;
  created_on: string;
};

export type ActivityLogItem = BaseEntity & {
  module: string;
  activity: string;
  reference_number: string;
  description: string;
  performed_by?: {
    id?: Uuid;
    username?: string;
    email?: string;
    first_name?: string;
    last_name?: string;
  } | null;
  activity_time: string;
};

export type SnapshotItem = BaseEntity & {
  generated_document?: {
    id: Uuid;
    code: string;
    file_name: string;
    checksum?: string;
  };
  snapshot_version: number;
  snapshot_json: Record<string, unknown>;
  created_on: string;
};
