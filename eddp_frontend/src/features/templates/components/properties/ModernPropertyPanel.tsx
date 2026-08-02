/**
 * ModernPropertyPanel - ProseMirror-based property panel
 * 
 * Displays formatting properties based on editor selection state,
 * replacing legacy Canvas-based property panels.
 */

import { Box, Stack, Typography, Paper, Divider, IconButton, ToggleButtonGroup, ToggleButton } from '@mui/material';
import { memo, useCallback } from 'react';
import { useEditorSelection, useFormattingState, useTextAlignment, useHeadingLevel } from '../../contexts/EditorSelectionContext';
import FormatBoldIcon from '@mui/icons-material/FormatBold';
import FormatItalicIcon from '@mui/icons-material/FormatItalic';
import FormatUnderlinedIcon from '@mui/icons-material/FormatUnderlined';
import FormatAlignLeftIcon from '@mui/icons-material/FormatAlignLeft';
import FormatAlignCenterIcon from '@mui/icons-material/FormatAlignCenter';
import FormatAlignRightIcon from '@mui/icons-material/FormatAlignRight';
import FormatAlignJustifyIcon from '@mui/icons-material/FormatAlignJustify';
import SettingsOutlinedIcon from '@mui/icons-material/SettingsOutlined';

interface ModernPropertyPanelProps {
  // Page-level properties (still needed)
  pageSize: string;
  orientation: string;
  onPageSizeChange: (size: any) => void;
  onOrientationChange: (orientation: any) => void;
}

export const ModernPropertyPanel = memo(function ModernPropertyPanel({
  pageSize,
  orientation,
  onPageSizeChange,
  onOrientationChange,
}: ModernPropertyPanelProps) {
  const { editor, contentType, hasSelection, selectionMode } = useEditorSelection();
  const formatting = useFormattingState();
  const alignment = useTextAlignment();
  const headingLevel = useHeadingLevel();

  const handleToggleFormat = useCallback((format: 'bold' | 'italic' | 'underline' | 'strike') => {
    if (!editor) return;
    
    switch (format) {
      case 'bold':
        editor.chain().focus().toggleBold().run();
        break;
      case 'italic':
        editor.chain().focus().toggleItalic().run();
        break;
      case 'underline':
        editor.chain().focus().toggleUnderline().run();
        break;
      case 'strike':
        editor.chain().focus().toggleStrike().run();
        break;
    }
  }, [editor]);

  const handleSetAlignment = useCallback((align: 'left' | 'center' | 'right' | 'justify') => {
    if (!editor) return;
    editor.chain().focus().setTextAlign(align).run();
  }, [editor]);

  const handleSetHeading = useCallback((level: 1 | 2 | 3 | 4 | 5 | 6) => {
    if (!editor) return;
    editor.chain().focus().setHeading({ level }).run();
  }, [editor]);

  const handleSetParagraph = useCallback(() => {
    if (!editor) return;
    editor.chain().focus().setParagraph().run();
  }, [editor]);

  // No selection - show document properties
  if (!hasSelection || selectionMode === 'none') {
    return (
      <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default' }}>
        <Stack spacing={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <SettingsOutlinedIcon fontSize="small" color="action" />
            <Typography variant="subtitle2" fontWeight={600}>
              Document Properties
            </Typography>
          </Box>
          
          <Divider />

          <Box>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              Page Size
            </Typography>
            <ToggleButtonGroup
              value={pageSize}
              exclusive
              onChange={(_, value) => value && onPageSizeChange(value)}
              size="small"
              fullWidth
            >
              <ToggleButton value="A4">A4</ToggleButton>
              <ToggleButton value="LETTER">Letter</ToggleButton>
              <ToggleButton value="LEGAL">Legal</ToggleButton>
            </ToggleButtonGroup>
          </Box>

          <Box>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              Orientation
            </Typography>
            <ToggleButtonGroup
              value={orientation}
              exclusive
              onChange={(_, value) => value && onOrientationChange(value)}
              size="small"
              fullWidth
            >
              <ToggleButton value="PORTRAIT">Portrait</ToggleButton>
              <ToggleButton value="LANDSCAPE">Landscape</ToggleButton>
            </ToggleButtonGroup>
          </Box>
        </Stack>
      </Paper>
    );
  }

  // Text selection - show formatting properties
  return (
    <Paper elevation={0} sx={{ p: 2, bgcolor: 'background.default' }}>
      <Stack spacing={2}>
        <Box display="flex" alignItems="center" gap={1}>
          <SettingsOutlinedIcon fontSize="small" color="action" />
          <Typography variant="subtitle2" fontWeight={600}>
            Text Formatting
          </Typography>
        </Box>
        
        <Divider />

        {/* Content Type */}
        <Box>
          <Typography variant="caption" color="text.secondary" gutterBottom>
            Type
          </Typography>
          <Typography variant="body2" fontWeight={500}>
            {contentType === 'heading' && headingLevel ? `Heading ${headingLevel}` : contentType}
          </Typography>
        </Box>

        {/* Block Type Controls */}
        {(contentType === 'paragraph' || contentType === 'heading') && (
          <Box>
            <Typography variant="caption" color="text.secondary" gutterBottom>
              Block Type
            </Typography>
            <ToggleButtonGroup
              value={contentType === 'heading' ? `h${headingLevel}` : 'paragraph'}
              exclusive
              onChange={(_, value) => {
                if (value === 'paragraph') {
                  handleSetParagraph();
                } else if (value?.startsWith('h')) {
                  const level = parseInt(value.substring(1)) as 1 | 2 | 3 | 4 | 5 | 6;
                  handleSetHeading(level);
                }
              }}
              size="small"
              fullWidth
            >
              <ToggleButton value="paragraph">P</ToggleButton>
              <ToggleButton value="h1">H1</ToggleButton>
              <ToggleButton value="h2">H2</ToggleButton>
              <ToggleButton value="h3">H3</ToggleButton>
            </ToggleButtonGroup>
          </Box>
        )}

        {/* Text Formatting */}
        <Box>
          <Typography variant="caption" color="text.secondary" gutterBottom>
            Text Style
          </Typography>
          <Stack direction="row" spacing={0.5}>
            <IconButton
              size="small"
              onClick={() => handleToggleFormat('bold')}
              color={formatting.bold ? 'primary' : 'default'}
              sx={{ bgcolor: formatting.bold ? 'action.selected' : 'transparent' }}
            >
              <FormatBoldIcon fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              onClick={() => handleToggleFormat('italic')}
              color={formatting.italic ? 'primary' : 'default'}
              sx={{ bgcolor: formatting.italic ? 'action.selected' : 'transparent' }}
            >
              <FormatItalicIcon fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              onClick={() => handleToggleFormat('underline')}
              color={formatting.underline ? 'primary' : 'default'}
              sx={{ bgcolor: formatting.underline ? 'action.selected' : 'transparent' }}
            >
              <FormatUnderlinedIcon fontSize="small" />
            </IconButton>
          </Stack>
        </Box>

        {/* Text Alignment */}
        <Box>
          <Typography variant="caption" color="text.secondary" gutterBottom>
            Alignment
          </Typography>
          <Stack direction="row" spacing={0.5}>
            <IconButton
              size="small"
              onClick={() => handleSetAlignment('left')}
              color={alignment === 'left' ? 'primary' : 'default'}
              sx={{ bgcolor: alignment === 'left' ? 'action.selected' : 'transparent' }}
            >
              <FormatAlignLeftIcon fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              onClick={() => handleSetAlignment('center')}
              color={alignment === 'center' ? 'primary' : 'default'}
              sx={{ bgcolor: alignment === 'center' ? 'action.selected' : 'transparent' }}
            >
              <FormatAlignCenterIcon fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              onClick={() => handleSetAlignment('right')}
              color={alignment === 'right' ? 'primary' : 'default'}
              sx={{ bgcolor: alignment === 'right' ? 'action.selected' : 'transparent' }}
            >
              <FormatAlignRightIcon fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              onClick={() => handleSetAlignment('justify')}
              color={alignment === 'justify' ? 'primary' : 'default'}
              sx={{ bgcolor: alignment === 'justify' ? 'action.selected' : 'transparent' }}
            >
              <FormatAlignJustifyIcon fontSize="small" />
            </IconButton>
          </Stack>
        </Box>

        {/* Selection Info */}
        <Box>
          <Typography variant="caption" color="text.secondary">
            Selection: {selectionMode} mode
          </Typography>
        </Box>
      </Stack>
    </Paper>
  );
});
