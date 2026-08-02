import PaletteOutlinedIcon from '@mui/icons-material/PaletteOutlined';
import SaveOutlinedIcon from '@mui/icons-material/SaveOutlined';
import { Button, FormControlLabel, MenuItem, Paper, Select, Stack, Switch, TextField, Typography } from '@mui/material';
import { useState } from 'react';

import { PageHeader } from '../components/common/PageHeader';
import { useSaveThemeSettings, useThemeSettings } from '../features/admin/hooks/useAdmin';
import { useAppDispatch, useAppSelector } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';
import { setDensity } from '../store/slices/adminSettingsSlice';
import { setThemeMode } from '../store/slices/themeSlice';

const DEFAULT_THEME_SETTINGS = {
  primaryColor: '#0057A8',
  secondaryColor: '#0C8B5F',
  density: 'comfortable' as 'compact' | 'comfortable',
};

type ThemeSettingsDraft = {
  primaryColor?: string;
  secondaryColor?: string;
  density?: 'compact' | 'comfortable';
};

export function ThemeSettingsPage() {
  const dispatch = useAppDispatch();
  const mode = useAppSelector((state) => state.theme.mode);
  const density = useAppSelector((state) => state.adminSettings.density);
  const query = useThemeSettings(mode);
  const mutation = useSaveThemeSettings();

  const [draft, setDraft] = useState<ThemeSettingsDraft>({});

  const settings = query.data ?? { ...DEFAULT_THEME_SETTINGS, density };
  const primaryColor = draft.primaryColor ?? settings.primaryColor;
  const secondaryColor = draft.secondaryColor ?? settings.secondaryColor;
  const compact = (draft.density ?? settings.density) === 'compact';

  return (
    <Stack spacing={3}>
      <PageHeader title="Theme Settings" subtitle="Control enterprise appearance, mode, and visual density." />

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack spacing={2}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <Select
              size="small"
              value={mode}
              onChange={(event) => dispatch(setThemeMode(event.target.value as 'light' | 'dark'))}
              sx={{ minWidth: 180 }}
            >
              <MenuItem value="light">Light</MenuItem>
              <MenuItem value="dark">Dark</MenuItem>
            </Select>
            <TextField
              label="Primary Color"
              value={primaryColor}
              onChange={(event) => setDraft((current) => ({ ...current, primaryColor: event.target.value }))}
              fullWidth
            />
            <TextField
              label="Secondary Color"
              value={secondaryColor}
              onChange={(event) => setDraft((current) => ({ ...current, secondaryColor: event.target.value }))}
              fullWidth
            />
          </Stack>

          <FormControlLabel
            control={
              <Switch
                checked={compact}
                onChange={(event) => {
                  const isCompact = event.target.checked;
                  setDraft((current) => ({
                    ...current,
                    density: isCompact ? 'compact' : 'comfortable',
                  }));
                  dispatch(setDensity(isCompact ? 'compact' : 'comfortable'));
                }}
              />
            }
            label="Compact Density"
          />

          <Typography variant="body2" color="text.secondary">
            Theme palette token persistence is staged in Sprint 10E and can be connected to backend configuration storage later.
          </Typography>

          <Stack direction="row" spacing={1}>
            <Button
              variant="contained"
              startIcon={<SaveOutlinedIcon />}
              disabled={mutation.isPending}
              onClick={async () => {
                try {
                  await mutation.mutateAsync({
                    mode,
                    primaryColor,
                    secondaryColor,
                    density: compact ? 'compact' : 'comfortable',
                  });
                  dispatch(enqueueNotification({ severity: 'success', message: 'Theme settings saved.' }));
                } catch {
                  dispatch(enqueueNotification({ severity: 'error', message: 'Failed to save theme settings.' }));
                }
              }}
            >
              {mutation.isPending ? 'Saving...' : 'Save Theme'}
            </Button>
            <Button
              variant="outlined"
              startIcon={<PaletteOutlinedIcon />}
              onClick={() => {
                setDraft({
                  primaryColor: DEFAULT_THEME_SETTINGS.primaryColor,
                  secondaryColor: DEFAULT_THEME_SETTINGS.secondaryColor,
                  density: 'comfortable',
                });
                dispatch(setThemeMode('light'));
                dispatch(setDensity('comfortable'));
                dispatch(enqueueNotification({ severity: 'info', message: 'Theme reset to enterprise defaults.' }));
              }}
            >
              Reset Defaults
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Stack>
  );
}
