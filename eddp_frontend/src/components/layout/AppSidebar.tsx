import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined';
import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined';
import SchemaOutlinedIcon from '@mui/icons-material/SchemaOutlined';
import HubOutlinedIcon from '@mui/icons-material/HubOutlined';
import ManageAccountsOutlinedIcon from '@mui/icons-material/ManageAccountsOutlined';
import AdminPanelSettingsOutlinedIcon from '@mui/icons-material/AdminPanelSettingsOutlined';
import LockPersonOutlinedIcon from '@mui/icons-material/LockPersonOutlined';
import PersonOutlinedIcon from '@mui/icons-material/PersonOutlined';
import CategoryOutlinedIcon from '@mui/icons-material/CategoryOutlined';
import RateReviewOutlinedIcon from '@mui/icons-material/RateReviewOutlined';
import {
  Divider,
  Drawer,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';

import { useAuth } from '../../auth/useAuth';
import { ROLE_GROUPS, ROUTES } from '../../constants/appConstants';
import { useAppDispatch, useAppSelector } from '../../hooks/reduxHooks';
import { setSidebarOpen } from '../../store/slices/appSlice';

const MENU_ITEMS = [
  { label: 'Dashboard', path: ROUTES.DASHBOARD, icon: DashboardOutlinedIcon },
  { label: 'Documents', path: ROUTES.DOCUMENTS, icon: DescriptionOutlinedIcon },
  { label: 'Variables', path: ROUTES.VARIABLES, icon: SchemaOutlinedIcon },
  { label: 'Document Create or Delete', path: ROUTES.TEMPLATES, icon: CategoryOutlinedIcon },
  { label: 'Document Approval', path: ROUTES.TEMPLATE_APPROVALS, icon: RateReviewOutlinedIcon },
  { label: 'Connectors', path: ROUTES.CONNECTORS, icon: HubOutlinedIcon },
  { label: 'User Management', path: ROUTES.USERS, icon: ManageAccountsOutlinedIcon, roles: ROLE_GROUPS.ADMIN },
  { label: 'Role Management', path: ROUTES.ROLES, icon: AdminPanelSettingsOutlinedIcon, roles: ROLE_GROUPS.ADMIN },
  { label: 'Permission Management', path: ROUTES.PERMISSIONS, icon: LockPersonOutlinedIcon, roles: ROLE_GROUPS.ADMIN },
  { label: 'Profile', path: ROUTES.PROFILE, icon: PersonOutlinedIcon },
] as const;

const DRAWER_WIDTH = 256;

export function AppSidebar() {
  const dispatch = useAppDispatch();
  const open = useAppSelector((state) => state.app.sidebarOpen);
  const { hasRole } = useAuth();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const location = useLocation();
  const navigate = useNavigate();

  const visibleMenu = MENU_ITEMS.filter((item) => {
    if (!('roles' in item) || !item.roles) {
      return true;
    }
    return item.roles.some((role) => hasRole(role));
  });

  const handleNavigate = (path: string): void => {
    navigate(path);
    if (isMobile) {
      dispatch(setSidebarOpen(false));
    }
  };

  return (
    <Drawer
      variant={isMobile ? 'temporary' : 'permanent'}
      open={open}
      onClose={() => dispatch(setSidebarOpen(false))}
      sx={{
        width: open ? DRAWER_WIDTH : 72,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: open ? DRAWER_WIDTH : 72,
          transition: 'width 200ms ease',
          overflowX: 'hidden',
        },
      }}
    >
      <Toolbar />
      <Divider />
      <List>
        {visibleMenu.map((item) => {
          const selected = location.pathname === item.path || location.pathname.startsWith(`${item.path}/`);
          const Icon = item.icon;
          return (
            <ListItemButton
              key={item.path}
              selected={selected}
              onClick={() => handleNavigate(item.path)}
              sx={{ minHeight: 46 }}
            >
              <ListItemIcon>
                <Icon fontSize="small" />
              </ListItemIcon>
              {open ? <ListItemText primary={item.label} /> : null}
            </ListItemButton>
          );
        })}
      </List>
    </Drawer>
  );
}
