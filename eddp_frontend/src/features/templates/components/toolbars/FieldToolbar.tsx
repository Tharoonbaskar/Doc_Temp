import { Stack, Divider, Select, MenuItem, Tooltip, Button } from '@mui/material';
import { memo } from 'react';
import CodeIcon from '@mui/icons-material/Code';

interface FieldToolbarProps {
  selectedField: string;
  labelPosition: string;
  valueFormat: string;
  onFieldChange: (field: string) => void;
  onLabelPositionChange: (position: string) => void;
  onValueFormatChange: (format: string) => void;
  onCodeEditor: () => void;
  availableFields?: Array<{ id: string; label: string; token: string }>;
}

export const FieldToolbar = memo(function FieldToolbar({
  selectedField,
  labelPosition,
  valueFormat,
  onFieldChange,
  onLabelPositionChange,
  onValueFormatChange,
  onCodeEditor,
  availableFields = [],
}: FieldToolbarProps) {
  return (
    <Stack direction="row" spacing={1} alignItems="center" sx={{ px: 2, py: 1, bgcolor: 'background.paper' }}>
      <Select
        size="small"
        value={selectedField}
        onChange={(e) => onFieldChange(e.target.value)}
        sx={{ minWidth: 180 }}
        displayEmpty
      >
        <MenuItem value="">Select Field...</MenuItem>
        {availableFields.map((field) => (
          <MenuItem key={field.id} value={field.token}>
            {field.label}
          </MenuItem>
        ))}
      </Select>

      <Divider orientation="vertical" flexItem />

      <Tooltip title="Label Position">
        <Select
          size="small"
          value={labelPosition}
          onChange={(e) => onLabelPositionChange(e.target.value)}
          sx={{ minWidth: 140 }}
        >
          <MenuItem value="none">Without label</MenuItem>
          <MenuItem value="left">Label at left</MenuItem>
          <MenuItem value="top">Label at top</MenuItem>
        </Select>
      </Tooltip>

      <Divider orientation="vertical" flexItem />

      <Tooltip title="Format Label">
        <Button size="small" variant="text" sx={{ minWidth: 100, textTransform: 'none' }}>
          Format label
        </Button>
      </Tooltip>

      <Tooltip title="Format Value">
        <Select
          size="small"
          value={valueFormat}
          onChange={(e) => onValueFormatChange(e.target.value)}
          sx={{ minWidth: 140 }}
        >
          <MenuItem value="none">No Format</MenuItem>
          <MenuItem value="currency">Currency</MenuItem>
          <MenuItem value="percentage">Percentage</MenuItem>
          <MenuItem value="date">Date</MenuItem>
          <MenuItem value="number">Number</MenuItem>
          <MenuItem value="uppercase">Uppercase</MenuItem>
          <MenuItem value="lowercase">Lowercase</MenuItem>
        </Select>
      </Tooltip>

      <Divider orientation="vertical" flexItem />

      <Tooltip title="Code Editor">
        <Button
          size="small"
          variant="outlined"
          startIcon={<CodeIcon />}
          onClick={onCodeEditor}
        >
          Code
        </Button>
      </Tooltip>
    </Stack>
  );
});
