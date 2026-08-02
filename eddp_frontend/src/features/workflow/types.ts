import type { BaseEntity, EntityStatus, Uuid } from '../shared/types';

export type WorkflowDocumentRef = {
  id: Uuid;
  code: string;
  name: string;
};

export type WorkflowItem = BaseEntity & {
  name: string;
  description: string;
  workflow_type: string;
  applicable_document?: WorkflowDocumentRef;
  version: number;
  is_default: boolean;
};

export type WorkflowPayload = {
  code: string;
  name: string;
  description: string;
  workflow_type: string;
  applicable_document_id: Uuid;
  version: number;
  is_default: boolean;
  status: EntityStatus;
};
