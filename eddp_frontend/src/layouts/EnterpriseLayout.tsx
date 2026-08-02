import LogoutOutlinedIcon from '@mui/icons-material/LogoutOutlined';
import PersonOutlinedIcon from '@mui/icons-material/PersonOutlined';
import { Box, Container, Divider, Menu, MenuItem, Stack, useMediaQuery, useTheme } from '@mui/material';
import { useMemo, useState } from 'react';
import { Outlet, useNavigate } from 'react-router-dom';

import { useAuth } from '../auth/useAuth';
import { ROUTES } from '../constants/appConstants';
import { AppBreadcrumbs } from '../components/layout/AppBreadcrumbs';
import { AppFooter } from '../components/layout/AppFooter';
import { AppHeader } from '../components/layout/AppHeader';
import { AppSidebar } from '../components/layout/AppSidebar';

export function EnterpriseLayout() {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const navigate = useNavigate();
  const { logout } = useAuth();
  const [profileAnchor, setProfileAnchor] = useState<HTMLElement | null>(null);

  const profileMenuOpen = useMemo(() => Boolean(profileAnchor), [profileAnchor]);

  const handleLogout = async (): Promise<void> => {
    setProfileAnchor(null);
    await logout();
    navigate(ROUTES.LOGIN, { replace: true });
  };

  return (
    <Stack direction="row" sx={{ minHeight: '100vh' }}>
      <AppSidebar />
      <Stack sx={{ flexGrow: 1 }}>
        <AppHeader onProfileClick={(anchor) => setProfileAnchor(anchor)} />
        <Container maxWidth={false} sx={{ py: 2, pl: isMobile ? 2 : 3, pr: isMobile ? 2 : 3, flexGrow: 1 }}>
          <Stack spacing={2}>
            <AppBreadcrumbs />
            <Divider />
            <Box>
              <Outlet />
            </Box>
          </Stack>
        </Container>
        <Container maxWidth={false}>
          <AppFooter />
        </Container>
      </Stack>

      <Menu
        anchorEl={profileAnchor}
        open={profileMenuOpen}
        onClose={() => setProfileAnchor(null)}
      >
        <MenuItem
          onClick={() => {
            setProfileAnchor(null);
            navigate(ROUTES.PROFILE);
          }}
        >
          <PersonOutlinedIcon fontSize="small" sx={{ mr: 1 }} />
          Profile
        </MenuItem>
        <MenuItem onClick={handleLogout}>
          <LogoutOutlinedIcon fontSize="small" sx={{ mr: 1 }} />
          Logout
        </MenuItem>
      </Menu>
    </Stack>
  );
}
