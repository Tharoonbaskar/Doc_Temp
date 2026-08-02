import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  List,
  ListItemButton,
  ListItemText,
  TextField,
  Box,
  Typography,
  Chip,
  Stack,
} from '@mui/material';

interface Variable {
  name: string;
  display_name: string;
  data_type: string;
  group?: {
    name: string;
  };
}

interface VariableInserterProps {
  open: boolean;
  onClose: () => void;
  onSelect: (variableName: string) => void;
  variables?: Variable[];
}

/**
 * Variable Inserter Modal
 * 
 * Simple modal to insert variables into paragraphs.
 * Similar to Zoho Creator's field insertion.
 * 
 * Usage:
 * 1. Click "Insert Variable" button in toolbar
 * 2. Search/select variable from list
 * 3. Variable token {{variable_name}} inserted at cursor
 */
export function VariableInserter({
  open,
  onClose,
  onSelect,
  variables = [],
}: VariableInserterProps) {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredVariables = variables.filter(
    (v) =>
      v.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      v.display_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleSelect = (variableName: string) => {
    onSelect(variableName);
    setSearchQuery('');
    onClose();
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Insert Variable</DialogTitle>
      <DialogContent>
        <Box sx={{ mb: 2 }}>
          <TextField
            autoFocus
            fullWidth
            size="small"
            placeholder="Search variables..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            sx={{ mb: 2 }}
          />
          <Typography variant="caption" color="text.secondary">
            Select a variable to insert into your paragraph. It will appear as{' '}
            <Chip label="{{variable_name}}" size="small" color="primary" sx={{ height: 20 }} />
          </Typography>
        </Box>

        {filteredVariables.length === 0 ? (
          <Box sx={{ py: 4, textAlign: 'center' }}>
            <Typography color="text.secondary">
              {searchQuery ? 'No variables found' : 'No variables available for this document'}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
              Add variables to your document first
            </Typography>
          </Box>
        ) : (
          <List sx={{ maxHeight: 400, overflow: 'auto' }}>
            {filteredVariables.map((variable) => (
              <ListItemButton
                key={variable.name}
                onClick={() => handleSelect(variable.name)}
                sx={{
                  borderRadius: 1,
                  mb: 0.5,
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
                        sx={{ height: 20, fontSize: '0.7rem' }}
                      />
                    </Stack>
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary">
                      {variable.group?.name && `${variable.group.name} • `}
                      {`{{${variable.name}}}`}
                    </Typography>
                  }
                />
              </ListItemButton>
            ))}
          </List>
        )}
      </DialogContent>
    </Dialog>
  );
}
