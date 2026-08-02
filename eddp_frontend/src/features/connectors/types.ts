import type { BaseEntity, EntityStatus } from '../shared/types';

export type ConnectorType = 'DATABASE' | 'API' | 'FILE' | 'QUEUE' | 'WEBHOOK';

export type ConnectorItem = BaseEntity & {
  name: string;
  connector_type: ConnectorType;
  description: string;
  host: string;
  port: number | null;
  database_name: string;
  username: string;
  password?: string;
  api_base_url: string;
  timeout: number;
  retry_count: number;
  is_active: boolean;
};

export type ConnectorPayload = {
  code: string;
  name: string;
  connector_type: ConnectorType;
  description: string;
  host: string;
  port: number | null;
  database_name: string;
  username: string;
  password?: string;
  api_base_url: string;
  timeout: number;
  retry_count: number;
  is_active: boolean;
  status: EntityStatus;
};
