import { Stack } from '@mui/material';
import { memo } from 'react';
import { PropertySection } from './PropertySection';
import { PropertyInput } from './PropertyInput';
import { PropertyToggle } from './PropertyToggle';
import { PropertySlider } from './PropertySlider';
import { PropertyColorPicker } from './PropertyColorPicker';
import TableChartOutlinedIcon from '@mui/icons-material/TableChartOutlined';
import FormatAlignLeftOutlinedIcon from '@mui/icons-material/FormatAlignLeftOutlined';
import PaletteOutlinedIcon from '@mui/icons-material/PaletteOutlined';

interface TablePropertiesProps {
  columns: string;
  binding: string;
  fontSize: number;
  borderColor: string;
  repeatingRows: boolean;
  tableHeader: boolean;
  tableFooter: boolean;
  alternating: boolean;
  visible: boolean;
  onColumnsChange: (columns: string) => void;
  onBindingChange: (binding: string) => void;
  onFontSizeChange: (size: number) => void;
  onBorderColorChange: (color: string) => void;
  onRepeatingRowsChange: (enabled: boolean) => void;
  onTableHeaderChange: (enabled: boolean) => void;
  onTableFooterChange: (enabled: boolean) => void;
  onAlternatingChange: (enabled: boolean) => void;
  onVisibleChange: (visible: boolean) => void;
}

export const TableProperties = memo(function TableProperties({
  columns,
  binding,
  fontSize,
  borderColor,
  repeatingRows,
  tableHeader,
  tableFooter,
  alternating,
  visible,
  onColumnsChange,
  onBindingChange,
  onFontSizeChange,
  onBorderColorChange,
  onRepeatingRowsChange,
  onTableHeaderChange,
  onTableFooterChange,
  onAlternatingChange,
  onVisibleChange,
}: TablePropertiesProps) {
  return (
    <Stack spacing={1.5}>
      <PropertySection title="Table Structure" icon={<TableChartOutlinedIcon fontSize="small" />} defaultExpanded>
        <PropertyInput
          label="Columns (comma-separated)"
          value={columns}
          onChange={(e) => onColumnsChange(e.target.value)}
          placeholder="Field, Value, Remarks"
        />
        <PropertyInput
          label="Binding Variable"
          value={binding}
          onChange={(e) => onBindingChange(e.target.value)}
          placeholder="e.g., {{Customer.Loans}}"
        />
      </PropertySection>

      <PropertySection title="Table Features" icon={<FormatAlignLeftOutlinedIcon fontSize="small" />} defaultExpanded>
        <PropertyToggle label="Repeating Rows" checked={repeatingRows} onChange={onRepeatingRowsChange} />
        <PropertyToggle label="Table Header" checked={tableHeader} onChange={onTableHeaderChange} />
        <PropertyToggle label="Table Footer" checked={tableFooter} onChange={onTableFooterChange} />
        <PropertyToggle label="Alternating Rows" checked={alternating} onChange={onAlternatingChange} />
      </PropertySection>

      <PropertySection title="Appearance" icon={<PaletteOutlinedIcon fontSize="small" />} defaultExpanded={false}>
        <PropertySlider label="Font Size" value={fontSize} onChange={onFontSizeChange} min={8} max={24} />
        <PropertyColorPicker label="Border Color" value={borderColor} onChange={onBorderColorChange} />
        <PropertyToggle label="Visible" checked={visible} onChange={onVisibleChange} />
      </PropertySection>
    </Stack>
  );
});
