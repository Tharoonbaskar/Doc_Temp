import { useEffect, useState, useRef } from 'react';
import {
  Paper,
  List,
  ListItemButton,
  ListItemText,
  Typography,
  Chip,
  Stack,
  Box,
} from '@mui/material';

interface Variable {
  name: string;
  display_name: string;
  data_type: string;
  group?: {
    name: string;
  };
}

interface VariableAutocompleteProps {
  variables: Variable[];
  anchorEl: HTMLElement | null;
  searchText: string;
  onSelect: (variableName: string) => void;
  onClose: () => void;
}

/**
 * Variable Autocomplete Dropdown
 * 
 * Shows a dropdown list of variables when user types $ character.
 * Similar to @mentions or slash commands.
 * 
 * Features:
 * - Filters variables as user types
 * - Positions near cursor
 * - Keyboard navigation (Arrow Up/Down, Enter to select, Esc to close)
 * - Shows variable metadata (type, group)
 */
export function VariableAutocomplete({
  variables,
  anchorEl,
  searchText,
  onSelect,
  onClose,
}: VariableAutocompleteProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const listRef = useRef<HTMLUListElement>(null);

  // Filter variables by search text
  const filteredVariables = variables.filter((v) => {
    if (!searchText) {
      // Show all variables when no search text (user just typed $)
      return true;
    }
    const search = searchText.toLowerCase();
    return (
      v.name.toLowerCase().includes(search) ||
      v.display_name.toLowerCase().includes(search)
    );
  });

  // Reset selected index when filtered list changes
  useEffect(() => {
    setSelectedIndex(0);
  }, [searchText]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!anchorEl) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex((prev) =>
            prev < filteredVariables.length - 1 ? prev + 1 : prev
          );
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex((prev) => (prev > 0 ? prev - 1 : 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (filteredVariables[selectedIndex]) {
            onSelect(filteredVariables[selectedIndex].name);
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [anchorEl, filteredVariables, selectedIndex, onSelect, onClose]);

  // Scroll selected item into view
  useEffect(() => {
    if (listRef.current) {
      const selectedElement = listRef.current.children[selectedIndex] as HTMLElement;
      selectedElement?.scrollIntoView({ block: 'nearest' });
    }
  }, [selectedIndex]);

  if (!anchorEl) {
    return null;
  }

  // Show message if no variables available
  if (variables.length === 0) {
    const rect = anchorEl.getBoundingClientRect();
    const position = {
      position: 'fixed' as const,
      top: rect.bottom + 4,
      left: rect.left,
      zIndex: 10000,
    };

    return (
      <Paper
        data-autocomplete-dropdown="true"
        sx={{
          ...position,
          minWidth: 300,
          boxShadow: 3,
          p: 2,
        }}
      >
        <Typography variant="body2" color="text.secondary">
          No variables available for this document.
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
          Add variables to your document first.
        </Typography>
      </Paper>
    );
  }

  if (filteredVariables.length === 0) {
    const rect = anchorEl.getBoundingClientRect();
    const position = {
      position: 'fixed' as const,
      top: rect.bottom + 4,
      left: rect.left,
      zIndex: 10000,
    };

    return (
      <Paper
        data-autocomplete-dropdown="true"
        sx={{
          ...position,
          minWidth: 300,
          boxShadow: 3,
          p: 2,
        }}
      >
        <Typography variant="body2" color="text.secondary">
          No variables matching "{searchText}"
        </Typography>
      </Paper>
    );
  }

  // Calculate position near cursor
  const rect = anchorEl.getBoundingClientRect();
  const position = {
    position: 'fixed' as const,
    top: rect.bottom + 4,
    left: rect.left,
    zIndex: 10000,
  };

  return (
    <Paper
      data-autocomplete-dropdown="true"
      sx={{
        ...position,
        maxWidth: 400,
        maxHeight: 300,
        overflow: 'auto',
        boxShadow: 3,
      }}
    >
      <Box sx={{ px: 1.5, py: 1, bgcolor: 'grey.100', borderBottom: 1, borderColor: 'divider' }}>
        <Typography variant="caption" color="text.secondary">
          Variables {searchText && `matching "${searchText}"`}
        </Typography>
      </Box>
      <List ref={listRef} sx={{ py: 0 }}>
        {filteredVariables.map((variable, index) => (
          <ListItemButton
            key={variable.name}
            selected={index === selectedIndex}
            onClick={() => onSelect(variable.name)}
            sx={{
              py: 1,
              borderLeft: index === selectedIndex ? 3 : 0,
              borderColor: 'primary.main',
              bgcolor: index === selectedIndex ? 'action.selected' : 'transparent',
              '&.Mui-selected': {
                bgcolor: 'action.selected',
              },
              '&:hover': {
                bgcolor: 'action.hover',
              },
            }}
          >
            <ListItemText
              primary={
                <Stack direction="row" spacing={1} alignItems="center">
                  <Typography variant="body2" fontWeight={500}>
                    {variable.display_name}
                  </Typography>
                  <Chip
                    label={variable.data_type}
                    size="small"
                    sx={{ height: 18, fontSize: '0.7rem' }}
                  />
                </Stack>
              }
              secondary={
                <Typography variant="caption" color="text.secondary">
                  {variable.group?.name && `${variable.group.name} • `}
                  {`$${variable.name}`}
                </Typography>
              }
            />
          </ListItemButton>
        ))}
      </List>
    </Paper>
  );
}
