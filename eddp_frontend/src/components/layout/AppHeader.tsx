import MenuIcon from '@mui/icons-material/Menu';
import DarkModeOutlinedIcon from '@mui/icons-material/DarkModeOutlined';
import LightModeOutlinedIcon from '@mui/icons-material/LightModeOutlined';
import {
  AppBar,
  Avatar,
  Box,
  IconButton,
  Stack,
  Toolbar,
  Tooltip,
  Typography,
} from '@mui/material';

import { APP_NAME } from '../../constants/appConstants';
import { useAuth } from '../../auth/useAuth';
import { useAppDispatch, useAppSelector } from '../../hooks/reduxHooks';
import { toggleSidebar } from '../../store/slices/appSlice';
import { toggleThemeMode } from '../../store/slices/themeSlice';
import { NotificationCenter } from './NotificationCenter';

type Props = {
  onProfileClick: (anchor: HTMLElement) => void;
};

export function AppHeader({ onProfileClick }: Props) {
  const dispatch = useAppDispatch();
  const mode = useAppSelector((state) => state.theme.mode);
  const { user } = useAuth();

  const initials = `${user?.first_name?.[0] ?? ''}${user?.last_name?.[0] ?? ''}`.toUpperCase() || 'U';

  return (
    <AppBar position="sticky" color="inherit">
      <Toolbar>
        <IconButton edge="start" onClick={() => dispatch(toggleSidebar())}>
          <MenuIcon />
        </IconButton>

        <Box sx={{ flexGrow: 1, ml: 1 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 700 }}>
            {APP_NAME}
          </Typography>
        </Box>

        <Stack direction="row" spacing={1} sx={{ alignItems: 'center' }}>
          <Tooltip title={mode === 'light' ? 'Switch to dark mode' : 'Switch to light mode'}>
            <IconButton onClick={() => dispatch(toggleThemeMode())}>
              {mode === 'light' ? <DarkModeOutlinedIcon /> : <LightModeOutlinedIcon />}
            </IconButton>
          </Tooltip>
          <NotificationCenter />
          <IconButton onClick={(event) => onProfileClick(event.currentTarget)}>
            <Avatar sx={{ width: 30, height: 30 }}>{initials}</Avatar>
          </IconButton>
        </Stack>
      </Toolbar>
    </AppBar>
  );
}
