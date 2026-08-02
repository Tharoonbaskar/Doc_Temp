import { useState, type ReactNode } from 'react';
import { Box, Stack, Typography, IconButton, Collapse } from '@mui/material';
import ExpandMoreOutlinedIcon from '@mui/icons-material/ExpandMoreOutlined';
import ExpandLessOutlinedIcon from '@mui/icons-material/ExpandLessOutlined';

interface PropertySectionProps {
  title: string;
  children: ReactNode;
  defaultExpanded?: boolean;
  icon?: ReactNode;
}

export function PropertySection({ title, children, defaultExpanded = true, icon }: PropertySectionProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  return (
    <Box sx={{ borderRadius: 1, border: '1px solid', borderColor: 'divider', overflow: 'hidden' }}>
      <Box
        onClick={() => setExpanded(!expanded)}
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          px: 1.5,
          py: 1,
          bgcolor: expanded ? 'action.hover' : 'background.paper',
          cursor: 'pointer',
          '&:hover': {
            bgcolor: 'action.hover',
          },
          transition: 'background-color 150ms',
        }}
      >
        <Stack direction="row" spacing={1} alignItems="center">
          {icon}
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {title}
          </Typography>
        </Stack>
        <IconButton size="small">
          {expanded ? <ExpandLessOutlinedIcon fontSize="small" /> : <ExpandMoreOutlinedIcon fontSize="small" />}
        </IconButton>
      </Box>
      <Collapse in={expanded}>
        <Box sx={{ p: 1.5 }}>
          <Stack spacing={1.5}>{children}</Stack>
        </Box>
      </Collapse>
    </Box>
  );
}
