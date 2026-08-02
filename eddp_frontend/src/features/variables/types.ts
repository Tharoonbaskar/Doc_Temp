import type { BaseEntity, EntityStatus, Uuid } from '../shared/types';

export type VariableGroupRef = {
  id: Uuid;
  code: string;
  name: string;
};

export type VariableItem = BaseEntity & {
  name: string;
  display_name: string;
  description: string;
  group_id?: Uuid;
  group?: VariableGroupRef;
  data_type: 'STRING' | 'INTEGER' | 'DECIMAL' | 'BOOLEAN' | 'DATE' | 'DATETIME' | 'JSON';
  source_type: 'STATIC' | 'INPUT' | 'CONNECTOR' | 'DERIVED' | 'RULE';
  source_reference: string;
  default_value: string;
  is_required: boolean;
  documents?: Array<{
    id: string;
    name: string;
    document_type: string;
  }>;
};

export type VariablePayload = {
  code: string;
  name: string;
  display_name: string;
  description: string;
  group_id: Uuid;
  data_type: VariableItem['data_type'];
  source_type: VariableItem['source_type'];
  source_reference: string;
  default_value: string;
  is_required: boolean;
  document_ids?: Uuid[];
  status: EntityStatus;
};
