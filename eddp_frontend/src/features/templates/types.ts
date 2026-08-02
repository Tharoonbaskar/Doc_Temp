import type { BaseEntity, Uuid } from '../shared/types';

export type TemplateStatus = 'DRAFT' | 'FOR_REVIEW' | 'APPROVED' | 'ARCHIVED';

export type TemplateDocumentRef = {
  id: Uuid;
  code: string;
  name: string;
};

export type TemplateItem = Omit<BaseEntity, 'status'> & {
  name: string;
  description: string;
  category: string;
  document_id?: Uuid;
  document?: TemplateDocumentRef;
  template_type: 'STATIC' | 'DYNAMIC' | 'COMPOSITE';
  content_type: string;
  prosemirror_json?: Record<string, unknown>;
  page_size?: 'A4' | 'A3' | 'LETTER' | 'LEGAL';
  page_orientation?: 'PORTRAIT' | 'LANDSCAPE';
  is_default: boolean;
  status: TemplateStatus;
  current_version?: number;
  version_count?: number;
  pending_draft_version?: number;
  has_pending_draft?: boolean;
  pending_draft_status?: 'DRAFT' | 'FOR_REVIEW' | 'APPROVED' | 'REJECTED';
  effective_date?: string;
  lifecycle_status?: 'ACTIVE' | 'INACTIVE';
  approved_by?: Uuid;
  approved_by_name?: string;
  approved_at?: string;
  review_comments?: string;
};

export type TemplatePayload = {
  code: string;
  name: string;
  description: string;
  category: string;
  document_id: Uuid;
  template_type: TemplateItem['template_type'];
  content_type: string;
  prosemirror_json?: Record<string, unknown>;
  page_size?: 'A4' | 'A3' | 'LETTER' | 'LEGAL';
  page_orientation?: 'PORTRAIT' | 'LANDSCAPE';
  is_default: boolean;
  status: TemplateStatus;
};

export type ParsedWordLayoutSection = {
  section_index: number;
  orientation: 'PORTRAIT' | 'LANDSCAPE';
  page_size: 'A4' | 'A3' | 'LETTER' | 'LEGAL' | 'CUSTOM';
  page_width_pt?: number;
  page_height_pt?: number;
  margins?: {
    top?: number;
    bottom?: number;
    left?: number;
    right?: number;
  };
  columns?: number;
};

export type ParsedWordLayoutRegion = {
  section_index: number;
  content: Record<string, unknown>[];
};

export type ParsedWordLayout = {
  title?: string;
  page_size?: 'A4' | 'A3' | 'LETTER' | 'LEGAL' | 'CUSTOM';
  page_orientation?: 'PORTRAIT' | 'LANDSCAPE';
  margins?: {
    top?: number;
    bottom?: number;
    left?: number;
    right?: number;
  };
  sections?: ParsedWordLayoutSection[];
  headers?: ParsedWordLayoutRegion[];
  footers?: ParsedWordLayoutRegion[];
  bookmarks?: Array<Record<string, unknown>>;
  page_number_fields?: number;
};

export type ParseWordDocumentResponse = {
  prosemirror_json: Record<string, unknown>;
  layout?: ParsedWordLayout;
  variable_summary?: Record<string, unknown>;
  semantic_sections?: Array<Record<string, unknown>>;
  validation_report?: Record<string, unknown>;
};

export type SendForReviewPayload = {
  review_comments?: string;
};

export type ApproveTemplatePayload = {
  effective_date: string;
  review_comments?: string;
};

export type SendBackPayload = {
  comments?: string;
};

// Version management types
export type ChangeType = 'ADDED' | 'MODIFIED' | 'DELETED';

export type SemanticChangeType =
  | 'TEXT_ADDED'
  | 'TEXT_REMOVED'
  | 'TEXT_MODIFIED'
  | 'VARIABLE_ADDED'
  | 'VARIABLE_REMOVED'
  | 'VARIABLE_MODIFIED'
  | 'IMAGE_ADDED'
  | 'IMAGE_REMOVED'
  | 'IMAGE_REPLACED'
  | 'IMAGE_RESIZED'
  | 'TABLE_STRUCTURE_CHANGED'
  | 'TABLE_CONTENT_CHANGED'
  | 'TABLE_STYLE_CHANGED'
  | 'HEADER_CHANGED'
  | 'FOOTER_CHANGED'
  | 'FONT_CHANGED'
  | 'FONT_SIZE_CHANGED'
  | 'FONT_COLOR_CHANGED'
  | 'BACKGROUND_CHANGED'
  | 'ALIGNMENT_CHANGED'
  | 'MARGIN_CHANGED'
  | 'PADDING_CHANGED'
  | 'PAGE_SIZE_CHANGED'
  | 'ORIENTATION_CHANGED'
  | 'SECTION_CHANGED'
  | 'PAGE_BREAK_CHANGED'
  | 'STYLE_CHANGED'
  | 'REPEAT_SECTION_CHANGED'
  | 'CONDITIONAL_BLOCK_CHANGED'
  | 'UNKNOWN_CHANGE';

export type ApprovalStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'REVERTED' | 'SENT_BACK' | 'RESOLVED';

export type ReviewAction = 'APPROVED' | 'REJECTED' | 'REVERTED' | 'SENT_BACK' | 'RESOLVED' | 'PENDING';

export type InlineDiffOp = 'equal' | 'insert' | 'delete';

export type InlineDiffSegment = {
  op: InlineDiffOp;
  text: string;
};

export type ElementChange = {
  id: Uuid;
  element_id: string;
  change_type: ChangeType;
  semantic_type?: SemanticChangeType;
  node_id?: string;
  page?: number;
  old_text?: string;
  new_text?: string;
  old_context_text?: string;
  new_context_text?: string;
  inline_segments?: InlineDiffSegment[];
  old_path?: string;
  new_path?: string;
  diff_granularity?: string;
  table_index?: number;
  row_index?: number;
  column_index?: number;
  old_style?: Record<string, unknown> | null;
  new_style?: Record<string, unknown> | null;
  old_value?: any;
  new_value?: any;
  approval_status: ApprovalStatus;
  reviewed_by?: Uuid;
  reviewed_by_name?: string;
  reviewed_at?: string;
  review_comment?: string;
  created_at: string;
  updated_at: string;
};

export type VersionInfo = {
  id: Uuid;
  template_id: Uuid;
  version_number: number;
  version_name: string;
  version_status: 'DRAFT' | 'FOR_REVIEW' | 'APPROVED' | 'REJECTED';
  template_json?: any;
  change_summary: string;
  base_version_id?: Uuid;
  created_at: string;
};

export type TemplateVersionDetailResponse = {
  template: TemplateItem;
  version: VersionInfo;
};

export type DiffSummary = {
  added: number;
  modified: number;
  deleted: number;
  total_changes: number;
};

export type VersionChangesResponse = {
  version: VersionInfo;
  changes: ElementChange[];
  diff_summary: DiffSummary;
};

export type ReviewChangePayload = {
  action: ReviewAction;
  comment?: string;
};

export type TemplatePdfVariableResolutionMode = 'RESOLVE_STRICT' | 'KEEP_UNRESOLVED';

export type TemplatePdfSecurityOptions = {
  password?: string;
  owner_password?: string;
  restrict_printing?: boolean;
  restrict_copy?: boolean;
};

export type TemplatePdfOptions = {
  page_size?: 'A4' | 'A3' | 'LETTER' | 'LEGAL';
  orientation?: 'PORTRAIT' | 'LANDSCAPE';
  margin_top_mm?: number;
  margin_bottom_mm?: number;
  margin_left_mm?: number;
  margin_right_mm?: number;
  header_height_mm?: number;
  footer_height_mm?: number;
  resolution_dpi?: number;
  watermark?: string;
  include_header_footer?: boolean;
  include_page_numbers?: boolean;
  variable_resolution_mode?: TemplatePdfVariableResolutionMode;
  font_embedding?: boolean;
  font_family?: string;
  header_text?: string;
  footer_text?: string;
  header_html?: string;
  footer_html?: string;
  preview_unresolved?: boolean;
  security?: TemplatePdfSecurityOptions;
};

export type TemplatePdfRequestPayload = {
  version?: string;
  variables?: Record<string, unknown>;
  pdf_options?: TemplatePdfOptions;
  metadata?: Record<string, unknown>;
  file_name?: string;
};

export type TemplatePdfPreviewResponse = {
  template_name: string;
  template_code: string;
  approved_version: string;
  status: string;
  generated_date: string;
  generated_by: string;
  page_count: number;
  preview_base64: string;
  mime_type: string;
  missing_variables?: string[];
  warnings?: string[];
  metadata?: Record<string, unknown>;
  options?: Record<string, unknown>;
  audit?: {
    audit_log_id?: string;
    activity_log_id?: string;
  };
};

export type TemplatePdfGenerateResponse = {
  template_name: string;
  template_code: string;
  approved_version: string;
  status: string;
  generated_date: string;
  generated_by: string;
  page_count: number;
  missing_variables?: string[];
  warnings?: string[];
  metadata?: Record<string, unknown>;
  options?: Record<string, unknown>;
  file_name?: string;
  file_size?: number;
  checksum?: string;
  file_url?: string;
  download_url?: string;
  audit?: {
    audit_log_id?: string;
    activity_log_id?: string;
  };
};

// Re-export editor orientation type from TemplateForm.
export type { Orientation } from './components/TemplateForm';

