import { TextField, type TextFieldProps } from '@mui/material';
import { memo } from 'react';

type PropertyInputProps = Omit<TextFieldProps, 'size' | 'variant'>;

export const PropertyInput = memo(function PropertyInput(props: PropertyInputProps) {
  return <TextField size="small" fullWidth {...props} />;
});
