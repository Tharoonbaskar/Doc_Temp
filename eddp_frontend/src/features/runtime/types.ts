import type { BaseEntity, EntityStatus, Uuid } from '../shared/types';

export type RuntimeGenerationRequestRef = {
  id: Uuid;
  code: string;
  request_id: Uuid;
  business_reference: string;
  correlation_id?: string;
  status: EntityStatus;
};

export type RuntimeDocumentRef = {
  id: Uuid;
  code: string;
  file_name: string;
  checksum?: string;
};

export type RuntimeGenerationRequestItem = BaseEntity & {
  request_id: Uuid;
  document?: {
    id: Uuid;
    code: string;
    name: string;
  };
  template_version?: {
    id: Uuid;
    code: string;
    version_number: number;
    version_name: string;
  };
  request_source: string;
  business_reference: string;
  correlation_id?: string;
  input_payload: Record<string, unknown>;
  requested_at: string;
  completed_at: string | null;
  processing_time_ms: number | null;
};

export type RuntimeExecutionHistoryItem = {
  stage_name?: string;
  stage_status?: string;
  sequence_no?: number;
  started_at?: string | null;
  completed_at?: string | null;
  duration_ms?: number;
  details_json?: Record<string, unknown>;
  stage?: string;
  status?: string;
  details?: Record<string, unknown>;
};

export type RuntimeGenerationMetric = {
  id: Uuid;
  code: string;
  output_format: 'PDF' | 'DOCX' | string;
  processing_time_ms: number;
  variable_count: number;
  rule_count: number;
  connector_count: number;
  recorded_on: string | null;
  metric_json: Record<string, unknown>;
};

export type RuntimeStatusResponse = {
  request_id: string;
  generation_request_id: string;
  business_reference: string;
  correlation_id?: string;
  status: EntityStatus | string;
  requested_at: string | null;
  completed_at: string | null;
  processing_time_ms: number | null;
  generated_document?: {
    id: string;
    code: string;
    file_name: string;
    file_path: string;
    file_type: string;
    file_size: number;
    checksum: string;
    generated_at: string | null;
  };
  download_url?: string;
  file_url?: string;
  generation_metric?: RuntimeGenerationMetric;
  execution_history?: RuntimeExecutionHistoryItem[];
};

export type RuntimeHistoryResponse = {
  business_reference: string;
  correlation_id?: string;
  count: number;
  history: Array<{
    request_id: string;
    generation_request_id: string;
    business_reference?: string;
    correlation_id?: string;
    status: string;
    request_source: string;
    requested_at: string | null;
    completed_at: string | null;
    processing_time_ms: number | null;
    generated_document?: {
      id: string;
      code: string;
      file_name: string;
      file_path: string;
      file_type: string;
      file_size: number;
      checksum: string;
      generated_at: string | null;
    };
    download_url?: string;
  }>;
};

export type RuntimePreviewPayload = {
  generation_request_id?: Uuid;
  document_id?: Uuid;
  variable_group_code?: string;
  rule_group_code?: string;
  connector_code?: string;
  connector_payload?: Record<string, unknown>;
  connectors?: Array<{
    connector_code: string;
    operation?: string;
    payload?: Record<string, unknown>;
    perform_validation?: boolean;
  }>;
  template_code?: string;
  template_version_code?: string;
  template_version_id?: Uuid | null;
  runtime_payload?: Record<string, unknown>;
  database_values?: Record<string, unknown>;
  connector_values?: Record<string, unknown>;
  computed_values?: Record<string, unknown>;
  render_options?: Record<string, unknown>;
  layout_options?: Record<string, unknown>;
  style_overrides?: string;
  business_reference?: string;
  correlation_id?: string;
  program_code?: string;
  module_name?: string;
  application_name?: string;
};

export type RuntimePreviewResponse = {
  generation_request_id: string;
  request_id: string;
  business_reference?: string;
  correlation_id?: string;
  template_code: string;
  template_version_code: string;
  html: string;
  page_size: string;
  orientation: string;
  execution_history?: RuntimeExecutionHistoryItem[];
};

export type RuntimeGeneratePayload = RuntimePreviewPayload & {
  output_format?: 'PDF' | 'DOCX';
  file_name?: string;
};

export type RuntimeGenerateResponse = {
  generation_request_id: string;
  request_id: string;
  business_reference?: string;
  correlation_id?: string;
  status: string;
  generated_document?: {
    id: string;
    code: string;
    file_name: string;
    file_path: string;
    file_type: string;
    file_size: number;
    checksum: string;
    generated_at: string | null;
  };
  download_url?: string;
  file_url?: string;
  execution_history?: RuntimeExecutionHistoryItem[];
};

export type RuntimeDownloadResponse = {
  request_id: string;
  business_reference: string;
  correlation_id?: string;
  status: string;
  generated_document?: {
    id: string;
    code: string;
    file_name: string;
    file_path: string;
    file_type: string;
    file_size: number;
    checksum: string;
    generated_at: string | null;
  };
  download_url?: string;
  file_url?: string;
};
