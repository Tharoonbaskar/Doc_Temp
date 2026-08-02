import DoneAllOutlinedIcon from '@mui/icons-material/DoneAllOutlined';
import NotificationsNoneIcon from '@mui/icons-material/NotificationsNone';
import CloseOutlinedIcon from '@mui/icons-material/CloseOutlined';
import {
  Badge,
  Box,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Menu,
  Tooltip,
  Typography,
} from '@mui/material';
import { useMemo, useState } from 'react';

import { useAppDispatch, useAppSelector } from '../../hooks/reduxHooks';
import { clearNotifications, dequeueNotification } from '../../store/slices/notificationSlice';

export function NotificationCenter() {
  const dispatch = useAppDispatch();
  const notifications = useAppSelector((state) => state.notifications.queue);
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);

  const open = useMemo(() => Boolean(anchor), [anchor]);

  return (
    <>
      <Tooltip title="Notifications">
        <IconButton onClick={(event) => setAnchor(event.currentTarget)}>
          <Badge color="error" badgeContent={notifications.length} max={99}>
            <NotificationsNoneIcon />
          </Badge>
        </IconButton>
      </Tooltip>

      <Menu
        anchorEl={anchor}
        open={open}
        onClose={() => setAnchor(null)}
        slotProps={{ paper: { sx: { width: 360, maxWidth: '90vw' } } }}
      >
        <Box sx={{ px: 2, py: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="subtitle2">Notifications</Typography>
          {notifications.length > 0 ? (
            <Tooltip title="Clear all notifications">
              <IconButton size="small" onClick={() => dispatch(clearNotifications())}>
                <DoneAllOutlinedIcon fontSize="small" />
              </IconButton>
            </Tooltip>
          ) : null}
        </Box>
        <Divider />

        {notifications.length === 0 ? (
          <Box sx={{ px: 2, py: 3 }}>
            <Typography variant="body2" color="text.secondary">
              No notifications available.
            </Typography>
          </Box>
        ) : (
          <List dense disablePadding>
            {[...notifications].reverse().map((item) => (
              <ListItem
                key={item.id}
                divider
                secondaryAction={
                  <IconButton edge="end" size="small" onClick={() => dispatch(dequeueNotification(item.id))}>
                    <CloseOutlinedIcon fontSize="small" />
                  </IconButton>
                }
              >
                <ListItemText
                  primary={<Typography variant="body2">{item.message}</Typography>}
                  secondary={
                    <Typography variant="caption" color="text.secondary">
                      {item.severity.toUpperCase()}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </Menu>
    </>
  );
}
