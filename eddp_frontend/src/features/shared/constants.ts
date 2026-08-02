export const STATUS_OPTIONS = ['ACTIVE', 'INACTIVE', 'DRAFT', 'PUBLISHED', 'ARCHIVED'] as const;

export const DOCUMENT_TYPE_OPTIONS = ['LETTER', 'REPORT', 'FORM', 'CONTRACT', 'CERTIFICATE'] as const;

export const OUTPUT_FORMAT_OPTIONS = ['PDF', 'DOCX', 'HTML', 'TXT', 'JSON'] as const;

export const TEMPLATE_TYPE_OPTIONS = ['STATIC', 'DYNAMIC', 'COMPOSITE'] as const;

export const DATA_TYPE_OPTIONS = ['STRING', 'INTEGER', 'DECIMAL', 'BOOLEAN', 'DATE', 'DATETIME', 'JSON'] as const;

export const SOURCE_TYPE_OPTIONS = ['STATIC', 'INPUT', 'CONNECTOR', 'DERIVED', 'RULE'] as const;
