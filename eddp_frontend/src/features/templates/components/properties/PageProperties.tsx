import { Stack } from '@mui/material';
import { memo } from 'react';
import { PropertySection } from './PropertySection';
import { PropertyDropdown } from './PropertyDropdown';
import { PropertyToggle } from './PropertyToggle';
import AspectRatioOutlinedIcon from '@mui/icons-material/AspectRatioOutlined';
import GridOnOutlinedIcon from '@mui/icons-material/GridOnOutlined';

interface PagePropertiesProps {
  pageSize: string;
  orientation: string;
  onPageSizeChange: (size: string) => void;
  onOrientationChange: (orientation: string) => void;
  gridEnabled: boolean;
  snapEnabled: boolean;
  guidesEnabled: boolean;
  onGridChange: (enabled: boolean) => void;
  onSnapChange: (enabled: boolean) => void;
  onGuidesChange: (enabled: boolean) => void;
}

export const PageProperties = memo(function PageProperties({
  pageSize,
  orientation,
  onPageSizeChange,
  onOrientationChange,
  gridEnabled,
  snapEnabled,
  guidesEnabled,
  onGridChange,
  onSnapChange,
  onGuidesChange,
}: PagePropertiesProps) {
  return (
    <Stack spacing={1.5}>
      <PropertySection title="Page Layout" icon={<AspectRatioOutlinedIcon fontSize="small" />} defaultExpanded>
        <PropertyDropdown
          label="Page Size"
          value={pageSize}
          onChange={onPageSizeChange}
          options={['A4', 'Letter', 'Legal']}
        />
        <PropertyDropdown
          label="Orientation"
          value={orientation}
          onChange={onOrientationChange}
          options={['PORTRAIT', 'LANDSCAPE']}
        />
      </PropertySection>

      <PropertySection title="Grid & Guides" icon={<GridOnOutlinedIcon fontSize="small" />} defaultExpanded={false}>
        <PropertyToggle label="Show Grid" checked={gridEnabled} onChange={onGridChange} />
        <PropertyToggle label="Snap to Grid" checked={snapEnabled} onChange={onSnapChange} />
        <PropertyToggle label="Alignment Guides" checked={guidesEnabled} onChange={onGuidesChange} />
      </PropertySection>
    </Stack>
  );
});
