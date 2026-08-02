import type { BaseEntity, EntityStatus, Uuid } from '../shared/types';

export type DocumentCategory = {
  id: Uuid;
  code: string;
  name: string;
};

export type DocumentItem = BaseEntity & {
  name: string;
  description: string;
  category_id?: Uuid;
  category?: DocumentCategory;
  document_type: 'LETTER' | 'REPORT' | 'FORM' | 'CONTRACT' | 'CERTIFICATE';
  business_module: 'PRIME' | 'EB';
  product: Array<'HOME LOAN' | 'PLOT LOAN' | 'LAP'> | string;
  output_format: 'PDF' | 'DOCX' | 'HTML' | 'TXT' | 'JSON';
};

export type DocumentPayload = {
  code: string;
  name: string;
  description: string;
  category_id: Uuid;
  document_type: DocumentItem['document_type'];
  business_module: DocumentItem['business_module'];
  product: Array<'HOME LOAN' | 'PLOT LOAN' | 'LAP'>;
  output_format: DocumentItem['output_format'];
  status: EntityStatus;
};
