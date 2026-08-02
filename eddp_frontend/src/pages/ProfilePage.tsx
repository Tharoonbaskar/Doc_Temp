import SaveOutlinedIcon from '@mui/icons-material/SaveOutlined';
import SecurityOutlinedIcon from '@mui/icons-material/SecurityOutlined';
import { Alert, Button, Paper, Stack, TextField, Typography } from '@mui/material';
import { useState } from 'react';

import { EmptyState } from '../components/common/EmptyState';
import { PageHeader } from '../components/common/PageHeader';
import { useChangePassword, useProfile, useUpdateProfile } from '../features/admin/hooks/useAdmin';
import { useAppDispatch } from '../hooks/reduxHooks';
import { enqueueNotification } from '../store/slices/notificationSlice';

type ProfileDraft = {
  first_name?: string;
  last_name?: string;
  email?: string;
};

export function ProfilePage() {
  const dispatch = useAppDispatch();
  const profileQuery = useProfile();
  const updateMutation = useUpdateProfile();
  const changePasswordMutation = useChangePassword();

  const [draft, setDraft] = useState<ProfileDraft>({});
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  if (profileQuery.isLoading) {
    return (
      <Stack spacing={3}>
        <PageHeader title="Profile" subtitle="Manage your enterprise profile and credentials." />
        <Typography color="text.secondary">Loading profile...</Typography>
      </Stack>
    );
  }

  if (!profileQuery.data) {
    return (
      <Stack spacing={3}>
        <PageHeader title="Profile" subtitle="Manage your enterprise profile and credentials." />
        <EmptyState title="Profile unavailable" description="Unable to load profile details from authentication service." />
      </Stack>
    );
  }

  const profile = profileQuery.data;
  const firstName = draft.first_name ?? profile.first_name ?? '';
  const lastName = draft.last_name ?? profile.last_name ?? '';
  const email = draft.email ?? profile.email ?? '';

  return (
    <Stack spacing={3}>
      <PageHeader title="Profile" subtitle="Manage your enterprise profile and credentials." />

      {profileQuery.error ? <Alert severity="error">Failed to load profile details.</Alert> : null}

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack spacing={2}>
          <Typography variant="subtitle1">Profile Information</Typography>
          <TextField label="Username" value={profile.username} disabled fullWidth />
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
            <TextField
              label="First Name"
              value={firstName}
              onChange={(event) => setDraft((current) => ({ ...current, first_name: event.target.value }))}
              fullWidth
            />
            <TextField
              label="Last Name"
              value={lastName}
              onChange={(event) => setDraft((current) => ({ ...current, last_name: event.target.value }))}
              fullWidth
            />
          </Stack>
          <TextField
            label="Email"
            value={email}
            onChange={(event) => setDraft((current) => ({ ...current, email: event.target.value }))}
            fullWidth
          />
          <Stack direction="row" spacing={1}>
            <Button
              variant="contained"
              startIcon={<SaveOutlinedIcon />}
              disabled={updateMutation.isPending}
              onClick={async () => {
                try {
                  await updateMutation.mutateAsync({
                    first_name: firstName,
                    last_name: lastName,
                    email,
                  });
                  dispatch(enqueueNotification({ severity: 'success', message: 'Profile updated successfully.' }));
                } catch {
                  dispatch(enqueueNotification({ severity: 'error', message: 'Failed to update profile.' }));
                }
              }}
            >
              {updateMutation.isPending ? 'Saving...' : 'Save Profile'}
            </Button>
          </Stack>
        </Stack>
      </Paper>

      <Paper variant="outlined" sx={{ p: 2 }}>
        <Stack spacing={2}>
          <Typography variant="subtitle1">Change Password</Typography>
          <TextField
            type="password"
            label="Current Password"
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
            fullWidth
          />
          <TextField
            type="password"
            label="New Password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            fullWidth
          />
          <TextField
            type="password"
            label="Confirm Password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            fullWidth
          />
          <Stack direction="row" spacing={1}>
            <Button
              variant="outlined"
              startIcon={<SecurityOutlinedIcon />}
              disabled={changePasswordMutation.isPending}
              onClick={async () => {
                if (!currentPassword || !newPassword || !confirmPassword) {
                  dispatch(enqueueNotification({ severity: 'error', message: 'All password fields are required.' }));
                  return;
                }
                try {
                  await changePasswordMutation.mutateAsync({
                    current_password: currentPassword,
                    new_password: newPassword,
                    confirm_password: confirmPassword,
                  });
                  setCurrentPassword('');
                  setNewPassword('');
                  setConfirmPassword('');
                  dispatch(enqueueNotification({ severity: 'success', message: 'Password changed successfully.' }));
                } catch {
                  dispatch(enqueueNotification({ severity: 'error', message: 'Failed to change password.' }));
                }
              }}
            >
              {changePasswordMutation.isPending ? 'Changing...' : 'Change Password'}
            </Button>
          </Stack>
        </Stack>
      </Paper>
    </Stack>
  );
}
