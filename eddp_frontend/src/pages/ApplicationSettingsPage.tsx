import SaveOutlinedIcon from '@mui/icons-material/SaveOutlined';
import { Button, FormControlLabel, Paper, Stack, Switch, TextField, Typography } from '@mui/material';
import { useState } from 'react';

import { PageHeader } from '../components/common/PageHeader';
import { useApplicationSettings, useSaveApplicationSettings } from '../features/admin/hooks/useAdmin';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';

const DEFAULT_APPLICATION_SETTINGS = {
  appName: '',
  apiBaseUrl: '',
  apiTimeoutMs: 15000,
  sessionTimeoutMs: 1800000,
  enableNotifications: true,
  dateFormat: 'YYYY-MM-DD HH:mm:ss',
};

type ApplicationSettingsDraft = {
  appName?: string;
  apiBaseUrl?: string;
  apiTimeoutMs?: number;
  sessionTimeoutMs?: number;
  enableNotifications?: boolean;
  dateFormat?: string;
};

export function ApplicationSettingsPage() {
  const dispatch = useAppDispatch();
  const query = useApplicationSettings();
  const mutation = useSaveApplicationSettings();

  const settings = query.data ?? DEFAULT_APPLICATION_SETTINGS;
  const [draft, setDraft] = useState<ApplicationSettingsDraft>({});

  const appName = draft.appName ?? settings.appName;
  const apiBaseUrl = draft.apiBaseUrl ?? settings.apiBaseUrl;
  const apiTimeoutMs = draft.apiTimeoutMs ?? settings.apiTimeoutMs;
  const sessionTimeoutMs = draft.sessionTimeoutMs ?? settings.sessionTimeoutMs;
  const enableNotifications = draft.enableNotifications ?? settings.enableNotifications;
  const dateFormat = draft.dateFormat ?? settings.dateFormat;

  return (
    <Stack spacing={3}>
      <PageHeader title="Application Settings" subtitle="Configure platform-level behavior and operational defaults." />

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack spacing={2}>
          <TextField
            label="Application Name"
            value={appName}
            onChange={(event) => setDraft((current) => ({ ...current, appName: event.target.value }))}
            fullWidth
          />
          <TextField
            label="API Base URL"
            value={apiBaseUrl}
            onChange={(event) => setDraft((current) => ({ ...current, apiBaseUrl: event.target.value }))}
            fullWidth
          />
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <TextField
              label="API Timeout (ms)"
              type="number"
              value={apiTimeoutMs}
              onChange={(event) =>
                setDraft((current) => ({ ...current, apiTimeoutMs: Number(event.target.value) || 0 }))
              }
              fullWidth
            />
            <TextField
              label="Session Timeout (ms)"
              type="number"
              value={sessionTimeoutMs}
              onChange={(event) =>
                setDraft((current) => ({ ...current, sessionTimeoutMs: Number(event.target.value) || 0 }))
              }
              fullWidth
            />
          </Stack>
          <TextField
            label="Date Format"
            value={dateFormat}
            onChange={(event) => setDraft((current) => ({ ...current, dateFormat: event.target.value }))}
            fullWidth
          />
          <FormControlLabel
            control={
              <Switch
                checked={enableNotifications}
                onChange={(event) =>
                  setDraft((current) => ({ ...current, enableNotifications: event.target.checked }))
                }
              />
            }
            label="Enable Notifications"
          />
          <Typography variant="body2" color="text.secondary">
            Settings are persisted in frontend configuration store until backend settings endpoint is available.
          </Typography>
          <Stack direction="row" spacing={1}>
            <Button
              variant="contained"
              startIcon={<SaveOutlinedIcon />}
              disabled={mutation.isPending || query.isLoading}
              onClick={async () => {
                try {
                  await mutation.mutateAsync({
                    appName,
                    apiBaseUrl,
                    apiTimeoutMs,
                    sessionTimeoutMs,
                    enableNotifications,
                    dateFormat,
                  });
                  dispatch(enqueueNotification({ severity: 'success', message: 'Application settings saved.' }));
                } catch {
                  dispatch(enqueueNotification({ severity: 'error', message: 'Failed to save settings.' }));
                }
              }}
            >
              {mutation.isPending ? 'Saving...' : 'Save Settings'}
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Stack>
  );
}
