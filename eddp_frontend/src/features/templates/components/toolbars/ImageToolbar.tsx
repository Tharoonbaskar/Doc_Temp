import { Box, Stack, IconButton, Divider, Tooltip, Button, Slider } from '@mui/material';
import { memo } from 'react';
import ImageIcon from '@mui/icons-material/Image';
import OpacityIcon from '@mui/icons-material/Opacity';
import RotateRightIcon from '@mui/icons-material/RotateRight';
import FlipToFrontIcon from '@mui/icons-material/FlipToFront';
import FlipToBackIcon from '@mui/icons-material/FlipToBack';

interface ImageToolbarProps {
  opacity: number;
  rotation: number;
  onReplaceImage: () => void;
  onOpacityChange: (opacity: number) => void;
  onRotationChange: (rotation: number) => void;
  onBringForward: () => void;
  onSendBackward: () => void;
}

export const ImageToolbar = memo(function ImageToolbar({
  opacity,
  rotation,
  onReplaceImage,
  onOpacityChange,
  onRotationChange,
  onBringForward,
  onSendBackward,
}: ImageToolbarProps) {
  return (
    <Stack direction="row" spacing={2} alignItems="center" sx={{ px: 2, py: 1, bgcolor: 'background.paper' }}>
      <Button size="small" variant="outlined" startIcon={<ImageIcon />} onClick={onReplaceImage}>
        Replace Image
      </Button>

      <Divider orientation="vertical" flexItem />

      <Box sx={{ minWidth: 150 }}>
        <Stack spacing={0.5}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <OpacityIcon fontSize="small" />
            <Slider
              size="small"
              value={opacity * 100}
              onChange={(_, v) => onOpacityChange((v as number) / 100)}
              min={0}
              max={100}
              sx={{ flexGrow: 1 }}
            />
          </Box>
        </Stack>
      </Box>

      <Box sx={{ minWidth: 150 }}>
        <Stack spacing={0.5}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <RotateRightIcon fontSize="small" />
            <Slider
              size="small"
              value={rotation}
              onChange={(_, v) => onRotationChange(v as number)}
              min={-180}
              max={180}
              sx={{ flexGrow: 1 }}
            />
          </Box>
        </Stack>
      </Box>

      <Divider orientation="vertical" flexItem />

      <Tooltip title="Bring Forward">
        <IconButton size="small" onClick={onBringForward}>
          <FlipToFrontIcon />
        </IconButton>
      </Tooltip>

      <Tooltip title="Send Backward">
        <IconButton size="small" onClick={onSendBackward}>
          <FlipToBackIcon />
        </IconButton>
      </Tooltip>
    </Stack>
  );
});
