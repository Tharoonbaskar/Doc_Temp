import { Paper } from '@mui/material';
import { memo } from 'react';
import { PageToolbar } from './PageToolbar';

interface ContextToolbarManagerProps {
  // Page props
  pageSize: string;
  orientation: string;
  gridEnabled: boolean;
  snapEnabled: boolean;
  guidesEnabled: boolean;
  onPageSizeChange: (size: string) => void;
  onOrientationChange: (orientation: string) => void;
  onGridToggle: () => void;
  onSnapToggle: () => void;
  onGuidesToggle: () => void;
  
}

export const ContextToolbarManager = memo(function ContextToolbarManager({
  pageSize,
  orientation,
  gridEnabled,
  snapEnabled,
  guidesEnabled,
  onPageSizeChange,
  onOrientationChange,
  onGridToggle,
  onSnapToggle,
  onGuidesToggle,
}: ContextToolbarManagerProps) {
  return (
    <Paper elevation={1} sx={{ borderBottom: '1px solid', borderColor: 'divider' }}>
      <PageToolbar
        pageSize={pageSize}
        orientation={orientation}
        gridEnabled={gridEnabled}
        snapEnabled={snapEnabled}
        guidesEnabled={guidesEnabled}
        onPageSizeChange={onPageSizeChange}
        onOrientationChange={onOrientationChange}
        onGridToggle={onGridToggle}
        onSnapToggle={onSnapToggle}
        onGuidesToggle={onGuidesToggle}
      />
    </Paper>
  );
});
