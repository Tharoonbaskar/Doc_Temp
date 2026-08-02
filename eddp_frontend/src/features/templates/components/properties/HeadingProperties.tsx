import { Stack } from '@mui/material';
import { memo } from 'react';
import { PropertySection } from './PropertySection';
import { PropertyInput } from './PropertyInput';
import { PropertyDropdown } from './PropertyDropdown';
import { PropertyColorPicker } from './PropertyColorPicker';
import { PropertySlider } from './PropertySlider';
import { PropertyToggle } from './PropertyToggle';
import TitleOutlinedIcon from '@mui/icons-material/TitleOutlined';
import FormatSizeOutlinedIcon from '@mui/icons-material/FormatSizeOutlined';
import PaletteOutlinedIcon from '@mui/icons-material/PaletteOutlined';

interface HeadingPropertiesProps {
  text: string;
  binding: string;
  fontSize: number;
  fontWeight: string;
  color: string;
  align: string;
  visible: boolean;
  onTextChange: (text: string) => void;
  onBindingChange: (binding: string) => void;
  onFontSizeChange: (size: number) => void;
  onFontWeightChange: (weight: string) => void;
  onColorChange: (color: string) => void;
  onAlignChange: (align: string) => void;
  onVisibleChange: (visible: boolean) => void;
}

export const HeadingProperties = memo(function HeadingProperties({
  text,
  binding,
  fontSize,
  fontWeight,
  color,
  align,
  visible,
  onTextChange,
  onBindingChange,
  onFontSizeChange,
  onFontWeightChange,
  onColorChange,
  onAlignChange,
  onVisibleChange,
}: HeadingPropertiesProps) {
  return (
    <Stack spacing={1.5}>
      <PropertySection title="Content" icon={<TitleOutlinedIcon fontSize="small" />} defaultExpanded>
        <PropertyInput
          label="Heading Text"
          value={text}
          onChange={(e) => onTextChange(e.target.value)}
        />
        <PropertyInput
          label="Binding Variable"
          value={binding}
          onChange={(e) => onBindingChange(e.target.value)}
          placeholder="e.g., {{Document.Title}}"
        />
      </PropertySection>

      <PropertySection title="Typography" icon={<FormatSizeOutlinedIcon fontSize="small" />} defaultExpanded>
        <PropertySlider label="Font Size" value={fontSize} onChange={onFontSizeChange} min={12} max={96} />
        <PropertyDropdown
          label="Font Weight"
          value={fontWeight}
          onChange={onFontWeightChange}
          options={['400', '500', '600', '700', '800']}
        />
        <PropertyDropdown
          label="Alignment"
          value={align}
          onChange={onAlignChange}
          options={['left', 'center', 'right']}
        />
      </PropertySection>

      <PropertySection title="Appearance" icon={<PaletteOutlinedIcon fontSize="small" />} defaultExpanded={false}>
        <PropertyColorPicker label="Color" value={color} onChange={onColorChange} />
        <PropertyToggle label="Visible" checked={visible} onChange={onVisibleChange} />
      </PropertySection>
    </Stack>
  );
});
