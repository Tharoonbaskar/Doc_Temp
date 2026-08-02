import { Box, Stack, TextField, Popover, IconButton } from '@mui/material';
import { useState, memo } from 'react';
import PaletteOutlinedIcon from '@mui/icons-material/PaletteOutlined';

interface PropertyColorPickerProps {
  label: string;
  value: string;
  onChange: (color: string) => void;
}

const PRESET_COLORS = [
  '#000000', '#FFFFFF', '#FF0000', '#00FF00', '#0000FF',
  '#FFFF00', '#FF00FF', '#00FFFF', '#808080', '#C0C0C0',
  '#800000', '#008000', '#000080', '#808000', '#800080',
  '#008080', '#FFA500', '#A52A2A', '#DEB887', '#5F9EA0',
];

export const PropertyColorPicker = memo(function PropertyColorPicker({
  label,
  value,
  onChange,
}: PropertyColorPickerProps) {
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  const handleClose = () => setAnchorEl(null);

  return (
    <>
      <Stack direction="row" spacing={1} alignItems="center">
        <TextField
          size="small"
          label={label}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          fullWidth
          slotProps={{
            input: {
              startAdornment: (
                <Box
                  sx={{
                    width: 24,
                    height: 24,
                    borderRadius: 1,
                    bgcolor: value || '#000000',
                    border: '1px solid',
                    borderColor: 'divider',
                    mr: 1,
                  }}
                />
              ),
            },
          }}
        />
        <IconButton size="small" onClick={(e) => setAnchorEl(e.currentTarget)}>
          <PaletteOutlinedIcon fontSize="small" />
        </IconButton>
      </Stack>

      <Popover
        open={Boolean(anchorEl)}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <Box sx={{ p: 2, maxWidth: 240 }}>
          <Stack direction="row" flexWrap="wrap" gap={1}>
            {PRESET_COLORS.map((color) => (
              <Box
                key={color}
                onClick={() => {
                  onChange(color);
                  handleClose();
                }}
                sx={{
                  width: 32,
                  height: 32,
                  borderRadius: 1,
                  bgcolor: color,
                  border: '2px solid',
                  borderColor: value === color ? 'primary.main' : 'divider',
                  cursor: 'pointer',
                  '&:hover': {
                    transform: 'scale(1.1)',
                    transition: 'transform 150ms',
                  },
                }}
              />
            ))}
          </Stack>
        </Box>
      </Popover>
    </>
  );
});
