import { Box, Stack, Typography } from '@mui/material';
import { memo } from 'react';
import { PageProperties } from './PageProperties';
import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined';

interface ContextualPropertyPanelProps {
  // Page-level props
  pageSize: string;
  orientation: string;
  gridEnabled: boolean;
  snapEnabled: boolean;
  guidesEnabled: boolean;
  onPageSizeChange: (size: string) => void;
  onOrientationChange: (orientation: string) => void;
  onGridChange: (enabled: boolean) => void;
  onSnapChange: (enabled: boolean) => void;
  onGuidesChange: (enabled: boolean) => void;
  
}

export const ContextualPropertyPanel = memo(function ContextualPropertyPanel({
  pageSize,
  orientation,
  gridEnabled,
  snapEnabled,
  guidesEnabled,
  onPageSizeChange,
  onOrientationChange,
  onGridChange,
  onSnapChange,
  onGuidesChange,
}: ContextualPropertyPanelProps) {
  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ bgcolor: 'primary.main', color: 'primary.contrastText', px: 1.5, py: 0.75 }}>
        <Stack direction="row" alignItems="center" spacing={1}>
          <SettingsOutlinedIcon fontSize="small" />
          <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
            Page Properties
          </Typography>
        </Stack>
      </Box>
      <Box sx={{ p: 1.5, overflowY: 'auto', flexGrow: 1 }}>
        <PageProperties
          pageSize={pageSize}
          orientation={orientation}
          gridEnabled={gridEnabled}
          snapEnabled={snapEnabled}
          guidesEnabled={guidesEnabled}
          onPageSizeChange={onPageSizeChange}
          onOrientationChange={onOrientationChange}
          onGridChange={onGridChange}
          onSnapChange={onSnapChange}
          onGuidesChange={onGuidesChange}
        />
      </Box>
    </Box>
  );
});
