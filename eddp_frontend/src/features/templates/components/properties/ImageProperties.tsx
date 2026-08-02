import { Stack } from '@mui/material';
import { memo } from 'react';
import { PropertySection } from './PropertySection';
import { PropertyInput } from './PropertyInput';
import { PropertyToggle } from './PropertyToggle';
import { PropertySlider } from './PropertySlider';
import ImageOutlinedIcon from '@mui/icons-material/ImageOutlined';
import AspectRatioOutlinedIcon from '@mui/icons-material/AspectRatioOutlined';
import OpacityOutlinedIcon from '@mui/icons-material/OpacityOutlined';

interface ImagePropertiesProps {
  imageUrl: string;
  width: number;
  height: number;
  opacity: number;
  rotation: number;
  visible: boolean;
  onImageUrlChange: (url: string) => void;
  onWidthChange: (width: number) => void;
  onHeightChange: (height: number) => void;
  onOpacityChange: (opacity: number) => void;
  onRotationChange: (rotation: number) => void;
  onVisibleChange: (visible: boolean) => void;
}

export const ImageProperties = memo(function ImageProperties({
  imageUrl,
  width,
  height,
  opacity,
  rotation,
  visible,
  onImageUrlChange,
  onWidthChange,
  onHeightChange,
  onOpacityChange,
  onRotationChange,
  onVisibleChange,
}: ImagePropertiesProps) {
  return (
    <Stack spacing={1.5}>
      <PropertySection title="Image Source" icon={<ImageOutlinedIcon fontSize="small" />} defaultExpanded>
        <PropertyInput
          label="Image URL"
          value={imageUrl}
          onChange={(e) => onImageUrlChange(e.target.value)}
          placeholder="https://example.com/image.png"
        />
      </PropertySection>

      <PropertySection title="Dimensions" icon={<AspectRatioOutlinedIcon fontSize="small" />} defaultExpanded>
        <PropertySlider label="Width" value={width} onChange={onWidthChange} min={50} max={800} />
        <PropertySlider label="Height" value={height} onChange={onHeightChange} min={50} max={800} />
      </PropertySection>

      <PropertySection title="Appearance" icon={<OpacityOutlinedIcon fontSize="small" />} defaultExpanded={false}>
        <PropertySlider label="Opacity" value={opacity * 100} onChange={(v) => onOpacityChange(v / 100)} min={0} max={100} />
        <PropertySlider label="Rotation" value={rotation} onChange={onRotationChange} min={-180} max={180} />
        <PropertyToggle label="Visible" checked={visible} onChange={onVisibleChange} />
      </PropertySection>
    </Stack>
  );
});
