import SearchIcon from '@mui/icons-material/Search';
import { InputAdornment, TextField, type SxProps, type Theme } from '@mui/material';

type Props = {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  sx?: SxProps<Theme>;
};

export function SearchBar({ value, onChange, placeholder, sx }: Props) {
  return (
    <TextField
      size="small"
      value={value}
      onChange={(event) => onChange(event.target.value)}
      placeholder={placeholder ?? 'Search'}
      sx={sx}
      slotProps={{
        input: {
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon fontSize="small" />
            </InputAdornment>
          ),
        },
      }}
    />
  );
}
