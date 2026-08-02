import { Stack, IconButton, Divider, Select, MenuItem, Tooltip } from '@mui/material';
import { memo } from 'react';
import GridOnOutlinedIcon from '@mui/icons-material/GridOnOutlined';
import GridOffOutlinedIcon from '@mui/icons-material/GridOffOutlined';
import AspectRatioOutlinedIcon from '@mui/icons-material/AspectRatioOutlined';

interface PageToolbarProps {
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

export const PageToolbar = memo(function PageToolbar({
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
}: PageToolbarProps) {
  return (
    <Stack direction="row" spacing={1} alignItems="center" sx={{ px: 2, py: 1, bgcolor: 'background.paper' }}>
      <Select
        size="small"
        value={pageSize}
        onChange={(e) => onPageSizeChange(e.target.value)}
        sx={{ minWidth: 100 }}
      >
        <MenuItem value="A4">A4</MenuItem>
        <MenuItem value="Letter">Letter</MenuItem>
        <MenuItem value="Legal">Legal</MenuItem>
      </Select>

      <Select
        size="small"
        value={orientation}
        onChange={(e) => onOrientationChange(e.target.value)}
        sx={{ minWidth: 120 }}
      >
        <MenuItem value="PORTRAIT">Portrait</MenuItem>
        <MenuItem value="LANDSCAPE">Landscape</MenuItem>
      </Select>

      <Divider orientation="vertical" flexItem />

      <Tooltip title={gridEnabled ? 'Hide Grid' : 'Show Grid'}>
        <IconButton size="small" onClick={onGridToggle} color={gridEnabled ? 'primary' : 'default'}>
          {gridEnabled ? <GridOnOutlinedIcon /> : <GridOffOutlinedIcon />}
        </IconButton>
      </Tooltip>

      <Tooltip title={snapEnabled ? 'Disable Snap' : 'Enable Snap'}>
        <IconButton size="small" onClick={onSnapToggle} color={snapEnabled ? 'primary' : 'default'}>
          <AspectRatioOutlinedIcon />
        </IconButton>
      </Tooltip>

      <Tooltip title="Alignment Guides">
        <IconButton size="small" onClick={onGuidesToggle} color={guidesEnabled ? 'primary' : 'default'}>
          <GridOnOutlinedIcon fontSize="small" />
        </IconButton>
      </Tooltip>
    </Stack>
  );
});
