import { configureStore } from '@reduxjs/toolkit';

import { activityLogsReducer } from './slices/activityLogsSlice';
import { adminSettingsReducer } from './slices/adminSettingsSlice';
import { appReducer } from './slices/appSlice';
import { auditLogsReducer } from './slices/auditLogsSlice';
import { authReducer } from './slices/authSlice';
import { connectorsReducer } from './slices/connectorsSlice';
import { documentsReducer } from './slices/documentsSlice';
import { notificationReducer } from './slices/notificationSlice';
import { permissionsReducer } from './slices/permissionsSlice';
import { rolesReducer } from './slices/rolesSlice';
import { rulesReducer } from './slices/rulesSlice';
import { runtimeReducer } from './slices/runtimeSlice';
import { snapshotsReducer } from './slices/snapshotsSlice';
import { themeReducer } from './slices/themeSlice';
import { templatesReducer } from './slices/templatesSlice';
import { usersReducer } from './slices/usersSlice';
import { variablesReducer } from './slices/variablesSlice';
import { workflowReducer } from './slices/workflowSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    app: appReducer,
    adminSettings: adminSettingsReducer,
    theme: themeReducer,
    notifications: notificationReducer,
    activityLogs: activityLogsReducer,
    auditLogs: auditLogsReducer,
    connectors: connectorsReducer,
    documents: documentsReducer,
    permissions: permissionsReducer,
    roles: rolesReducer,
    rules: rulesReducer,
    runtime: runtimeReducer,
    snapshots: snapshotsReducer,
    templates: templatesReducer,
    users: usersReducer,
    variables: variablesReducer,
    workflow: workflowReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
