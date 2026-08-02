import { Stack } from '@mui/material';
import { memo } from 'react';
import { PropertySection } from './PropertySection';
import { PropertyInput } from './PropertyInput';
import { PropertyDropdown } from './PropertyDropdown';
import { PropertyColorPicker } from './PropertyColorPicker';
import { PropertyToggle } from './PropertyToggle';
import { PropertySlider } from './PropertySlider';
import FormatSizeOutlinedIcon from '@mui/icons-material/FormatSizeOutlined';
import PaletteOutlinedIcon from '@mui/icons-material/PaletteOutlined';
import AspectRatioOutlinedIcon from '@mui/icons-material/AspectRatioOutlined';
import VisibilityOutlinedIcon from '@mui/icons-material/VisibilityOutlined';
import CodeOutlinedIcon from '@mui/icons-material/CodeOutlined';

interface TextPropertiesProps {
  text: string;
  binding: string;
  fontSize: number;
  fontWeight: string;
  color: string;
  backgroundColor: string;
  align: string;
  padding: number;
  opacity: number;
  rotation: number;
  visible: boolean;
  onTextChange: (text: string) => void;
  onBindingChange: (binding: string) => void;
  onFontSizeChange: (size: number) => void;
  onFontWeightChange: (weight: string) => void;
  onColorChange: (color: string) => void;
  onBackgroundColorChange: (color: string) => void;
  onAlignChange: (align: string) => void;
  onPaddingChange: (padding: number) => void;
  onOpacityChange: (opacity: number) => void;
  onRotationChange: (rotation: number) => void;
  onVisibleChange: (visible: boolean) => void;
}

export const TextProperties = memo(function TextProperties({
  text,
  binding,
  fontSize,
  fontWeight,
  color,
  backgroundColor,
  align,
  padding,
  opacity,
  rotation,
  visible,
  onTextChange,
  onBindingChange,
  onFontSizeChange,
  onFontWeightChange,
  onColorChange,
  onBackgroundColorChange,
  onAlignChange,
  onPaddingChange,
  onOpacityChange,
  onRotationChange,
  onVisibleChange,
}: TextPropertiesProps) {
  return (
    <Stack spacing={1.5}>
      <PropertySection title="Content" icon={<CodeOutlinedIcon fontSize="small" />} defaultExpanded>
        <PropertyInput
          label="Text"
          value={text}
          onChange={(e) => onTextChange(e.target.value)}
          multiline
          minRows={2}
        />
        <PropertyInput
          label="Binding Variable"
          value={binding}
          onChange={(e) => onBindingChange(e.target.value)}
          placeholder="e.g., {{Customer.Name}}"
        />
      </PropertySection>

      <PropertySection title="Typography" icon={<FormatSizeOutlinedIcon fontSize="small" />} defaultExpanded>
        <PropertySlider label="Font Size" value={fontSize} onChange={onFontSizeChange} min={8} max={72} />
        <PropertyDropdown
          label="Font Weight"
          value={fontWeight}
          onChange={onFontWeightChange}
          options={['400', '500', '600', '700']}
        />
        <PropertyDropdown
          label="Alignment"
          value={align}
          onChange={onAlignChange}
          options={['left', 'center', 'right', 'justify']}
        />
      </PropertySection>

      <PropertySection title="Appearance" icon={<PaletteOutlinedIcon fontSize="small" />} defaultExpanded={false}>
        <PropertyColorPicker label="Text Color" value={color} onChange={onColorChange} />
        <PropertyColorPicker label="Background" value={backgroundColor} onChange={onBackgroundColorChange} />
        <PropertySlider label="Opacity" value={opacity * 100} onChange={(v) => onOpacityChange(v / 100)} min={0} max={100} />
      </PropertySection>

      <PropertySection title="Layout" icon={<AspectRatioOutlinedIcon fontSize="small" />} defaultExpanded={false}>
        <PropertySlider label="Padding" value={padding} onChange={onPaddingChange} min={0} max={50} />
        <PropertySlider label="Rotation" value={rotation} onChange={onRotationChange} min={-180} max={180} />
      </PropertySection>

      <PropertySection title="Visibility" icon={<VisibilityOutlinedIcon fontSize="small" />} defaultExpanded={false}>
        <PropertyToggle label="Visible" checked={visible} onChange={onVisibleChange} />
      </PropertySection>
    </Stack>
  );
});
