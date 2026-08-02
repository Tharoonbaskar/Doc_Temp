import { FormControlLabel, Switch } from '@mui/material';
import { memo } from 'react';

interface PropertyToggleProps {
  label: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled?: boolean;
}

export const PropertyToggle = memo(function PropertyToggle({
  label,
  checked,
  onChange,
  disabled,
}: PropertyToggleProps) {
  return (
    <FormControlLabel
      control={<Switch checked={checked} onChange={(e) => onChange(e.target.checked)} disabled={disabled} />}
      label={label}
    />
  );
});
