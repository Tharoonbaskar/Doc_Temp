import { Stack, IconButton, Divider, Tooltip, Button } from '@mui/material';
import { memo } from 'react';
import TableChartIcon from '@mui/icons-material/TableChart';
import ViewColumnIcon from '@mui/icons-material/ViewColumn';
import TableRowsIcon from '@mui/icons-material/TableRows';
import BorderAllIcon from '@mui/icons-material/BorderAll';
import CodeIcon from '@mui/icons-material/Code';

interface TableToolbarProps {
  hasHeader: boolean;
  hasFooter: boolean;
  alternatingRows: boolean;
  onHeaderToggle: () => void;
  onFooterToggle: () => void;
  onAlternatingToggle: () => void;
  onInsertColumn: () => void;
  onDeleteColumn: () => void;
  onInsertRow: () => void;
  onDeleteRow: () => void;
  onBindingEditor: () => void;
}

export const TableToolbar = memo(function TableToolbar({
  hasHeader,
  hasFooter,
  alternatingRows,
  onHeaderToggle,
  onFooterToggle,
  onAlternatingToggle,
  onInsertColumn,
  onDeleteColumn,
  onInsertRow,
  onDeleteRow,
  onBindingEditor,
}: TableToolbarProps) {
  return (
    <Stack direction="row" spacing={1} alignItems="center" sx={{ px: 2, py: 1, bgcolor: 'background.paper' }}>
      <Tooltip title={hasHeader ? 'Remove Header' : 'Add Header'}>
        <IconButton size="small" onClick={onHeaderToggle} color={hasHeader ? 'primary' : 'default'}>
          <TableChartIcon />
        </IconButton>
      </Tooltip>

      <Tooltip title={hasFooter ? 'Remove Footer' : 'Add Footer'}>
        <IconButton size="small" onClick={onFooterToggle} color={hasFooter ? 'primary' : 'default'}>
          <TableChartIcon />
        </IconButton>
      </Tooltip>

      <Tooltip title="Alternating Rows">
        <IconButton size="small" onClick={onAlternatingToggle} color={alternatingRows ? 'primary' : 'default'}>
          <BorderAllIcon />
        </IconButton>
      </Tooltip>

      <Divider orientation="vertical" flexItem />

      <Tooltip title="Insert Column">
        <Button size="small" variant="outlined" onClick={onInsertColumn} startIcon={<ViewColumnIcon />}>
          Column
        </Button>
      </Tooltip>

      <Tooltip title="Delete Column">
        <IconButton size="small" onClick={onDeleteColumn}>
          <ViewColumnIcon color="error" />
        </IconButton>
      </Tooltip>

      <Divider orientation="vertical" flexItem />

      <Tooltip title="Insert Row">
        <Button size="small" variant="outlined" onClick={onInsertRow} startIcon={<TableRowsIcon />}>
          Row
        </Button>
      </Tooltip>

      <Tooltip title="Delete Row">
        <IconButton size="small" onClick={onDeleteRow}>
          <TableRowsIcon color="error" />
        </IconButton>
      </Tooltip>

      <Divider orientation="vertical" flexItem />

      <Tooltip title="Binding Editor">
        <Button size="small" variant="outlined" startIcon={<CodeIcon />} onClick={onBindingEditor}>
          Binding
        </Button>
      </Tooltip>
    </Stack>
  );
});
