import type { BaseEntity, EntityStatus, Uuid } from '../shared/types';

export type RuleType = 'VALIDATION' | 'TRANSFORMATION' | 'ELIGIBILITY' | 'CALCULATION' | 'ROUTING';

export type RuleGroupRef = {
  id: Uuid;
  code: string;
  name: string;
  priority?: number;
};

export type RuleItem = BaseEntity & {
  name: string;
  description: string;
  expression: string;
  rule_type: RuleType;
  execution_order: number;
  is_active: boolean;
  rule_group_id?: Uuid;
  rule_group?: RuleGroupRef;
};

export type RulePayload = {
  code: string;
  rule_group_id: Uuid;
  name: string;
  description: string;
  expression: string;
  rule_type: RuleType;
  execution_order: number;
  is_active: boolean;
  status: EntityStatus;
};
