import { Suspense, lazy } from 'react';
import type { ComponentType, LazyExoticComponent, ReactElement } from 'react';
import {
  Navigate,
  createBrowserRouter,
  type RouteObject,
} from 'react-router-dom';

import { ProtectedRoute } from '../auth/ProtectedRoute';
import {
  ADMIN_ROUTES,
  CONNECTOR_ROUTES,
  DOCUMENT_ROUTES,
  ROLE_GROUPS,
  ROUTES,
  TEMPLATE_ROUTES,
  TEMPLATE_APPROVAL_ROUTES,
  VARIABLE_ROUTES,
} from '../constants/appConstants';
import { EnterpriseLayout } from '../layouts/EnterpriseLayout';

const ApplicationSettingsPage = lazy(() =>
  import('../pages/ApplicationSettingsPage').then((module) => ({ default: module.ApplicationSettingsPage })),
);
const ConnectorCreatePage = lazy(() =>
  import('../pages/ConnectorCreatePage').then((module) => ({ default: module.ConnectorCreatePage })),
);
const ConnectorEditPage = lazy(() =>
  import('../pages/ConnectorEditPage').then((module) => ({ default: module.ConnectorEditPage })),
);
const ConnectorsListPage = lazy(() =>
  import('../pages/ConnectorsListPage').then((module) => ({ default: module.ConnectorsListPage })),
);
const ConnectorViewPage = lazy(() =>
  import('../pages/ConnectorViewPage').then((module) => ({ default: module.ConnectorViewPage })),
);
const DashboardPage = lazy(() =>
  import('../pages/DashboardPage').then((module) => ({ default: module.DashboardPage })),
);
const LoginPage = lazy(() =>
  import('../pages/LoginPage').then((module) => ({ default: module.LoginPage })),
);
const NotFoundPage = lazy(() =>
  import('../pages/NotFoundPage').then((module) => ({ default: module.NotFoundPage })),
);
const UnauthorizedPage = lazy(() =>
  import('../pages/UnauthorizedPage').then((module) => ({ default: module.UnauthorizedPage })),
);
const DocumentsListPage = lazy(() =>
  import('../pages/DocumentsListPage').then((module) => ({ default: module.DocumentsListPage })),
);
const DocumentCreatePage = lazy(() =>
  import('../pages/DocumentCreatePage').then((module) => ({ default: module.DocumentCreatePage })),
);
const DocumentEditPage = lazy(() =>
  import('../pages/DocumentEditPage').then((module) => ({ default: module.DocumentEditPage })),
);
const DocumentViewPage = lazy(() =>
  import('../pages/DocumentViewPage').then((module) => ({ default: module.DocumentViewPage })),
);
const TemplatesListPage = lazy(() =>
  import('../pages/TemplatesListPage').then((module) => ({ default: module.TemplatesListPage })),
);
const TemplateCreatePage = lazy(() =>
  import('../pages/TemplateCreatePage').then((module) => ({ default: module.TemplateCreatePage })),
);
const TemplateEditPage = lazy(() =>
  import('../pages/TemplateEditPage').then((module) => ({ default: module.TemplateEditPage })),
);
const TemplateVersionEditPage = lazy(() =>
  import('../pages/TemplateVersionEditPage').then((module) => ({ default: module.TemplateVersionEditPage })),
);
const TemplateViewPage = lazy(() =>
  import('../pages/TemplateViewPage').then((module) => ({ default: module.TemplateViewPage })),
);
const TemplateReviewPage = lazy(() =>
  import('../pages/TemplateReviewPage').then((module) => ({ default: module.TemplateReviewPage })),
);
const TemplateApprovalsListPage = lazy(() =>
  import('../pages/TemplateApprovalsListPage').then((module) => ({ default: module.TemplateApprovalsListPage })),
);
const TemplatePdfStudioPage = lazy(() =>
  import('../pages/TemplatePdfStudioPage').then((module) => ({ default: module.TemplatePdfStudioPage })),
);
const VariablesListPage = lazy(() =>
  import('../pages/VariablesListPage').then((module) => ({ default: module.VariablesListPage })),
);
const VariableCreatePage = lazy(() =>
  import('../pages/VariableCreatePage').then((module) => ({ default: module.VariableCreatePage })),
);
const VariableEditPage = lazy(() =>
  import('../pages/VariableEditPage').then((module) => ({ default: module.VariableEditPage })),
);
const VariableViewPage = lazy(() =>
  import('../pages/VariableViewPage').then((module) => ({ default: module.VariableViewPage })),
);
const PermissionManagementPage = lazy(() =>
  import('../pages/PermissionManagementPage').then((module) => ({ default: module.PermissionManagementPage })),
);
const ProfilePage = lazy(() =>
  import('../pages/ProfilePage').then((module) => ({ default: module.ProfilePage })),
);
const RolesManagementPage = lazy(() =>
  import('../pages/RolesManagementPage').then((module) => ({ default: module.RolesManagementPage })),
);
const SystemHealthPage = lazy(() =>
  import('../pages/SystemHealthPage').then((module) => ({ default: module.SystemHealthPage })),
);
const ThemeSettingsPage = lazy(() =>
  import('../pages/ThemeSettingsPage').then((module) => ({ default: module.ThemeSettingsPage })),
);
const UserManagementPage = lazy(() =>
  import('../pages/UserManagementPage').then((module) => ({ default: module.UserManagementPage })),
);

const renderLazyPage = (
  PageComponent: LazyExoticComponent<ComponentType>,
): ReactElement => (
  <Suspense
    fallback={(
      <div style={{ padding: '1.5rem', textAlign: 'center', color: '#5f6368' }}>
        Loading page...
      </div>
    )}
  >
    <PageComponent />
  </Suspense>
);

const protectedChildren: RouteObject[] = [
  { path: ROUTES.DASHBOARD, element: renderLazyPage(DashboardPage) },
  { path: DOCUMENT_ROUTES.LIST, element: renderLazyPage(DocumentsListPage) },
  { path: DOCUMENT_ROUTES.CREATE, element: renderLazyPage(DocumentCreatePage) },
  { path: `${ROUTES.DOCUMENTS}/:id`, element: renderLazyPage(DocumentViewPage) },
  { path: `${ROUTES.DOCUMENTS}/:id/edit`, element: renderLazyPage(DocumentEditPage) },
  { path: TEMPLATE_ROUTES.LIST, element: renderLazyPage(TemplatesListPage) },
  { path: TEMPLATE_ROUTES.CREATE, element: renderLazyPage(TemplateCreatePage) },
  { path: `${ROUTES.TEMPLATES}/:id`, element: renderLazyPage(TemplateViewPage) },
  { path: `${ROUTES.TEMPLATES}/:id/edit`, element: renderLazyPage(TemplateEditPage) },
  { path: `${ROUTES.TEMPLATES}/:id/pdf`, element: renderLazyPage(TemplatePdfStudioPage) },
  { path: `${ROUTES.TEMPLATES}/:id/versions/:versionNumber/edit`, element: renderLazyPage(TemplateVersionEditPage) },
  { path: `${ROUTES.TEMPLATES}/:id/review`, element: renderLazyPage(TemplateReviewPage) },
  { path: `${ROUTES.TEMPLATES}/:id/versions/:versionNumber/review`, element: renderLazyPage(TemplateVersionEditPage) },
  { path: TEMPLATE_APPROVAL_ROUTES.LIST, element: renderLazyPage(TemplateApprovalsListPage) },
  { path: VARIABLE_ROUTES.LIST, element: renderLazyPage(VariablesListPage) },
  { path: VARIABLE_ROUTES.CREATE, element: renderLazyPage(VariableCreatePage) },
  { path: `${ROUTES.VARIABLES}/:id`, element: renderLazyPage(VariableViewPage) },
  { path: `${ROUTES.VARIABLES}/:id/edit`, element: renderLazyPage(VariableEditPage) },
  { path: CONNECTOR_ROUTES.LIST, element: renderLazyPage(ConnectorsListPage) },
  { path: CONNECTOR_ROUTES.CREATE, element: renderLazyPage(ConnectorCreatePage) },
  { path: `${ROUTES.CONNECTORS}/:id`, element: renderLazyPage(ConnectorViewPage) },
  { path: `${ROUTES.CONNECTORS}/:id/edit`, element: renderLazyPage(ConnectorEditPage) },
  {
    path: ADMIN_ROUTES.PROFILE,
    element: renderLazyPage(ProfilePage),
  },
  {
    path: ADMIN_ROUTES.SYSTEM_HEALTH,
    element: renderLazyPage(SystemHealthPage),
  },
  {
    path: ADMIN_ROUTES.USERS,
    element: (
      <ProtectedRoute requiredRoles={ROLE_GROUPS.ADMIN}>
        {renderLazyPage(UserManagementPage)}
      </ProtectedRoute>
    ),
  },
  {
    path: ADMIN_ROUTES.ROLES,
    element: (
      <ProtectedRoute requiredRoles={ROLE_GROUPS.ADMIN}>
        {renderLazyPage(RolesManagementPage)}
      </ProtectedRoute>
    ),
  },
  {
    path: ADMIN_ROUTES.PERMISSIONS,
    element: (
      <ProtectedRoute requiredRoles={ROLE_GROUPS.ADMIN}>
        {renderLazyPage(PermissionManagementPage)}
      </ProtectedRoute>
    ),
  },
  {
    path: ADMIN_ROUTES.APPLICATION_SETTINGS,
    element: (
      <ProtectedRoute requiredRoles={ROLE_GROUPS.ADMIN}>
        {renderLazyPage(ApplicationSettingsPage)}
      </ProtectedRoute>
    ),
  },
  {
    path: ADMIN_ROUTES.THEME_SETTINGS,
    element: (
      <ProtectedRoute requiredRoles={ROLE_GROUPS.ADMIN}>
        {renderLazyPage(ThemeSettingsPage)}
      </ProtectedRoute>
    ),
  },
  {
    path: ROUTES.SETTINGS,
    element: (
      <ProtectedRoute requiredRoles={ROLE_GROUPS.ADMIN}>
        {renderLazyPage(ApplicationSettingsPage)}
      </ProtectedRoute>
    ),
  },
];

export const appRouter = createBrowserRouter([
  {
    path: ROUTES.ROOT,
    element: <Navigate to={ROUTES.DASHBOARD} replace />,
  },
  {
    path: ROUTES.LOGIN,
    element: renderLazyPage(LoginPage),
  },
  {
    path: ROUTES.UNAUTHORIZED,
    element: renderLazyPage(UnauthorizedPage),
  },
  {
    path: ROUTES.ROOT,
    element: (
      <ProtectedRoute>
        <EnterpriseLayout />
      </ProtectedRoute>
    ),
    children: protectedChildren,
  },
  {
    path: ROUTES.NOT_FOUND,
    element: renderLazyPage(NotFoundPage),
  },
  {
    path: '*',
    element: <Navigate to={ROUTES.NOT_FOUND} replace />,
  },
]);
