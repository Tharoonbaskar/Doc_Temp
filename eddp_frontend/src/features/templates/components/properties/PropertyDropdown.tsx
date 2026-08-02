import { FormControl, InputLabel, Select, MenuItem } from '@mui/material';
import { memo } from 'react';

interface PropertyDropdownProps<T extends string = string> {
  label: string;
  value: T;
  onChange: (value: T) => void;
  options: readonly T[] | { value: T; label: string }[];
  helperText?: string;
  error?: boolean;
}

export const PropertyDropdown = memo(function PropertyDropdown<T extends string = string>({
  label,
  value,
  onChange,
  options,
  error,
}: PropertyDropdownProps<T>) {
  const labelId = `property-${label.toLowerCase().replace(/\s+/g, '-')}`;

  return (
    <FormControl size="small" fullWidth error={error}>
      <InputLabel id={labelId}>{label}</InputLabel>
      <Select
        labelId={labelId}
        label={label}
        value={value}
        onChange={(event) => onChange(event.target.value as T)}
      >
        {options.map((option) => {
          const optionValue = typeof option === 'string' ? option : option.value;
          const optionLabel = typeof option === 'string' ? option : option.label;
          return (
            <MenuItem key={optionValue} value={optionValue}>
              {optionLabel}
            </MenuItem>
          );
        })}
      </Select>
    </FormControl>
  );
}) as <T extends string = string>(props: PropertyDropdownProps<T>) => React.ReactElement;
