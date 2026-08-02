import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import { Breadcrumbs, Link as MuiLink, Typography } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';

const ROUTE_LABELS: Record<string, string> = {
  'dashboard': 'Home',
  'documents': 'Documents',
  'templates': 'Document Create or Delete',
  'template-approvals': 'Document Approval',
  'variables': 'Variables',
  'connectors': 'Connectors',
  'users': 'User Management',
  'roles': 'Role Management',
  'permissions': 'Permission Management',
  'profile': 'Profile',
  'settings': 'Settings',
  'new': 'Create New',
  'edit': 'Edit',
  'review': 'Review',
};

export function AppBreadcrumbs() {
  const location = useLocation();
  const segments = location.pathname.split('/').filter(Boolean);

  return (
    <Breadcrumbs separator={<NavigateNextIcon fontSize="small" />} aria-label="breadcrumb">
      <MuiLink component={Link} underline="hover" color="inherit" to="/dashboard">
        Home
      </MuiLink>
      {segments.map((segment, index) => {
        const to = `/${segments.slice(0, index + 1).join('/')}`;
        const label = ROUTE_LABELS[segment] || segment.charAt(0).toUpperCase() + segment.slice(1);
        const isLast = index === segments.length - 1;

        if (isLast) {
          return (
            <Typography color="text.primary" key={to}>
              {label}
            </Typography>
          );
        }

        return (
          <MuiLink component={Link} underline="hover" color="inherit" to={to} key={to}>
            {label}
          </MuiLink>
        );
      })}
    </Breadcrumbs>
  );
}
