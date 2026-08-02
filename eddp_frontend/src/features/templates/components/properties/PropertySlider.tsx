import { Stack, Typography, Slider } from '@mui/material';
import { memo } from 'react';

interface PropertySliderProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  min?: number;
  max?: number;
  step?: number;
  valueLabelDisplay?: 'auto' | 'on' | 'off';
}

export const PropertySlider = memo(function PropertySlider({
  label,
  value,
  onChange,
  min = 0,
  max = 100,
  step = 1,
  valueLabelDisplay = 'auto',
}: PropertySliderProps) {
  return (
    <Stack spacing={0.5}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="caption" color="text.secondary">
          {label}
        </Typography>
        <Typography variant="caption" sx={{ fontWeight: 600 }}>
          {value}
        </Typography>
      </Stack>
      <Slider
        value={value}
        onChange={(_, newValue) => onChange(newValue as number)}
        min={min}
        max={max}
        step={step}
        valueLabelDisplay={valueLabelDisplay}
        size="small"
      />
    </Stack>
  );
});
