import { Stack, IconButton, Divider, Select, MenuItem, Tooltip, ToggleButtonGroup, ToggleButton, Button } from '@mui/material';
import { memo } from 'react';
import FormatBoldIcon from '@mui/icons-material/FormatBold';
import FormatItalicIcon from '@mui/icons-material/FormatItalic';
import FormatUnderlinedIcon from '@mui/icons-material/FormatUnderlined';
import FormatAlignLeftIcon from '@mui/icons-material/FormatAlignLeft';
import FormatAlignCenterIcon from '@mui/icons-material/FormatAlignCenter';
import FormatAlignRightIcon from '@mui/icons-material/FormatAlignRight';
import FormatAlignJustifyIcon from '@mui/icons-material/FormatAlignJustify';
import FormatListBulletedIcon from '@mui/icons-material/FormatListBulleted';
import FormatListNumberedIcon from '@mui/icons-material/FormatListNumbered';
import LinkIcon from '@mui/icons-material/Link';
import UndoIcon from '@mui/icons-material/Undo';
import RedoIcon from '@mui/icons-material/Redo';
import DataObjectIcon from '@mui/icons-material/DataObject';

interface ParagraphToolbarProps {
  fontSize: number;
  fontWeight: string;
  fontStyle?: string;
  textDecoration?: string;
  textAlign: string;
  onFontSizeChange: (size: number) => void;
  onTextAlignChange: (align: string) => void;
  onBoldToggle: () => void;
  onItalicToggle: () => void;
  onUnderlineToggle: () => void;
  onInsertVariable?: () => void;
  onUndo?: () => void;
  onRedo?: () => void;
}

export const ParagraphToolbar = memo(function ParagraphToolbar({
  fontSize,
  fontWeight,
  fontStyle = 'normal',
  textDecoration = 'none',
  textAlign,
  onFontSizeChange,
  onTextAlignChange,
  onBoldToggle,
  onItalicToggle,
  onUnderlineToggle,
  onInsertVariable,
  onUndo,
  onRedo,
}: ParagraphToolbarProps) {
  return (
    <Stack direction="row" spacing={1} alignItems="center" sx={{ px: 2, py: 1, bgcolor: 'background.paper' }}>
      {/* Insert Variable Button - Primary action */}
      {onInsertVariable && (
        <>
          <Button
            variant="outlined"
            size="small"
            startIcon={<DataObjectIcon />}
            onClick={onInsertVariable}
            sx={{ textTransform: 'none' }}
          >
            Insert Variable
          </Button>
          <Divider orientation="vertical" flexItem />
        </>
      )}

      <Select
        size="small"
        value={fontSize}
        onChange={(e) => onFontSizeChange(Number(e.target.value))}
        sx={{ minWidth: 80 }}
      >
        {[8, 10, 12, 14, 16, 18, 20, 24, 28, 32, 36, 48, 72].map((size) => (
          <MenuItem key={size} value={size}>
            {size}
          </MenuItem>
        ))}
      </Select>

      <Divider orientation="vertical" flexItem />

      <Tooltip title="Bold">
        <IconButton size="small" onClick={onBoldToggle} color={fontWeight === '700' ? 'primary' : 'default'}>
          <FormatBoldIcon />
        </IconButton>
      </Tooltip>

      <Tooltip title="Italic">
        <IconButton size="small" onClick={onItalicToggle} color={fontStyle === 'italic' ? 'primary' : 'default'}>
          <FormatItalicIcon />
        </IconButton>
      </Tooltip>

      <Tooltip title="Underline">
        <IconButton size="small" onClick={onUnderlineToggle} color={textDecoration === 'underline' ? 'primary' : 'default'}>
          <FormatUnderlinedIcon />
        </IconButton>
      </Tooltip>

      <Divider orientation="vertical" flexItem />

      <ToggleButtonGroup
        value={textAlign}
        exclusive
        onChange={(_, value) => value && onTextAlignChange(value)}
        size="small"
      >
        <ToggleButton value="left">
          <FormatAlignLeftIcon fontSize="small" />
        </ToggleButton>
        <ToggleButton value="center">
          <FormatAlignCenterIcon fontSize="small" />
        </ToggleButton>
        <ToggleButton value="right">
          <FormatAlignRightIcon fontSize="small" />
        </ToggleButton>
        <ToggleButton value="justify">
          <FormatAlignJustifyIcon fontSize="small" />
        </ToggleButton>
      </ToggleButtonGroup>

      <Divider orientation="vertical" flexItem />

      <Tooltip title="Bullet List">
        <IconButton size="small">
          <FormatListBulletedIcon />
        </IconButton>
      </Tooltip>

      <Tooltip title="Numbered List">
        <IconButton size="small">
          <FormatListNumberedIcon />
        </IconButton>
      </Tooltip>

      <Tooltip title="Insert Link">
        <IconButton size="small">
          <LinkIcon />
        </IconButton>
      </Tooltip>

      <Divider orientation="vertical" flexItem />

      {onUndo && (
        <Tooltip title="Undo">
          <IconButton size="small" onClick={onUndo}>
            <UndoIcon />
          </IconButton>
        </Tooltip>
      )}

      {onRedo && (
        <Tooltip title="Redo">
          <IconButton size="small" onClick={onRedo}>
            <RedoIcon />
          </IconButton>
        </Tooltip>
      )}
    </Stack>
  );
});
