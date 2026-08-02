export const APP_NAME = 'EDDP Enterprise';
export const SESSION_TIMEOUT_MS = 30 * 60 * 1000;
export const API_TIMEOUT_MS = 15_000;

export const ROUTES = {
  ROOT: '/',
  DASHBOARD: '/dashboard',
  DOCUMENTS: '/documents',
  TEMPLATES: '/templates',
  TEMPLATE_PDF_STUDIO: '/templates/:id/pdf',
  TEMPLATE_APPROVALS: '/template-approvals',
  VARIABLES: '/variables',
  CONNECTORS: '/connectors',
  RULES: '/rules',
  WORKFLOW: '/workflow',
  RUNTIME: '/runtime',
  DOCUMENT_PREVIEW: '/runtime/document-preview',
  DOCUMENT_GENERATION: '/runtime/document-generation',
  DOWNLOAD_CENTER: '/runtime/download-center',
  AUDIT_LOGS: '/runtime/audit-logs',
  ACTIVITY_LOGS: '/runtime/activity-logs',
  SNAPSHOTS: '/runtime/snapshots',
  GOVERNANCE: '/governance',
  USERS: '/users',
  ROLES: '/roles',
  PERMISSIONS: '/permissions',
  PROFILE: '/profile',
  APPLICATION_SETTINGS: '/settings/application',
  THEME_SETTINGS: '/settings/theme',
  AUDIT_VIEWER: '/audit-viewer',
  SYSTEM_HEALTH: '/system-health',
  SETTINGS: '/settings',
  LOGIN: '/login',
  UNAUTHORIZED: '/unauthorized',
  NOT_FOUND: '/404',
} as const;

export const DOCUMENT_ROUTES = {
  LIST: ROUTES.DOCUMENTS,
  CREATE: `${ROUTES.DOCUMENTS}/new`,
  view: (id: string) => `${ROUTES.DOCUMENTS}/${id}`,
  edit: (id: string) => `${ROUTES.DOCUMENTS}/${id}/edit`,
} as const;

export const TEMPLATE_ROUTES = {
  LIST: ROUTES.TEMPLATES,
  CREATE: `${ROUTES.TEMPLATES}/new`,
  view: (id: string) => `${ROUTES.TEMPLATES}/${id}`,
  edit: (id: string) => `${ROUTES.TEMPLATES}/${id}/edit`,
  pdfStudio: (id: string) => `${ROUTES.TEMPLATES}/${id}/pdf`,
  editVersion: (id: string, versionNumber: number) => `${ROUTES.TEMPLATES}/${id}/versions/${versionNumber}/edit`,
  review: (id: string) => `${ROUTES.TEMPLATES}/${id}/review`,
} as const;

export const TEMPLATE_APPROVAL_ROUTES = {
  LIST: ROUTES.TEMPLATE_APPROVALS,
  review: (id: string) => `${ROUTES.TEMPLATES}/${id}/review`,
  reviewVersion: (id: string, versionNumber: number) => `${ROUTES.TEMPLATES}/${id}/versions/${versionNumber}/review`,
} as const;

export const VARIABLE_ROUTES = {
  LIST: ROUTES.VARIABLES,
  CREATE: `${ROUTES.VARIABLES}/new`,
  view: (id: string) => `${ROUTES.VARIABLES}/${id}`,
  edit: (id: string) => `${ROUTES.VARIABLES}/${id}/edit`,
} as const;

export const CONNECTOR_ROUTES = {
  LIST: ROUTES.CONNECTORS,
  CREATE: `${ROUTES.CONNECTORS}/new`,
  view: (id: string) => `${ROUTES.CONNECTORS}/${id}`,
  edit: (id: string) => `${ROUTES.CONNECTORS}/${id}/edit`,
} as const;

export const RULE_ROUTES = {
  LIST: ROUTES.RULES,
  CREATE: `${ROUTES.RULES}/new`,
  view: (id: string) => `${ROUTES.RULES}/${id}`,
  edit: (id: string) => `${ROUTES.RULES}/${id}/edit`,
} as const;

export const WORKFLOW_ROUTES = {
  LIST: ROUTES.WORKFLOW,
  CREATE: `${ROUTES.WORKFLOW}/new`,
  view: (id: string) => `${ROUTES.WORKFLOW}/${id}`,
  edit: (id: string) => `${ROUTES.WORKFLOW}/${id}/edit`,
} as const;

export const RUNTIME_ROUTES = {
  LIST: ROUTES.RUNTIME,
  PREVIEW: ROUTES.DOCUMENT_PREVIEW,
  GENERATION: ROUTES.DOCUMENT_GENERATION,
  DOWNLOAD_CENTER: ROUTES.DOWNLOAD_CENTER,
  AUDIT_LOGS: ROUTES.AUDIT_LOGS,
  ACTIVITY_LOGS: ROUTES.ACTIVITY_LOGS,
  SNAPSHOTS: ROUTES.SNAPSHOTS,
  status: (requestId: string) => `${ROUTES.RUNTIME}/status/${requestId}`,
} as const;

export const ADMIN_ROUTES = {
  USERS: ROUTES.USERS,
  ROLES: ROUTES.ROLES,
  PERMISSIONS: ROUTES.PERMISSIONS,
  PROFILE: ROUTES.PROFILE,
  APPLICATION_SETTINGS: ROUTES.APPLICATION_SETTINGS,
  THEME_SETTINGS: ROUTES.THEME_SETTINGS,
  AUDIT_VIEWER: ROUTES.AUDIT_VIEWER,
  SYSTEM_HEALTH: ROUTES.SYSTEM_HEALTH,
} as const;

export const TOKEN_STORAGE_KEYS = {
  ACCESS: 'eddp_access_token',
  REFRESH: 'eddp_refresh_token',
  USER: 'eddp_user',
} as const;

export const ROLE_GROUPS = {
  ADMIN: ['admin', 'administrator', 'superadmin', 'super_admin', 'system_admin'],
  GOVERNANCE: ['governance_admin', 'compliance_officer', 'auditor', 'admin'],
} as const;
