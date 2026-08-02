import { Table, TableBody, TableCell, TableHead, TableRow, Typography } from '@mui/material';
import type { ReactNode } from 'react';

type DataColumn<T> = {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
};

type Props<T> = {
  rows: T[];
  columns: Array<DataColumn<T>>;
  emptyMessage?: string;
};

export function DataTable<T>({ rows, columns, emptyMessage }: Props<T>) {
  if (rows.length === 0) {
    return <Typography color="text.secondary">{emptyMessage ?? 'No records available.'}</Typography>;
  }

  return (
    <Table size="small">
      <TableHead>
        <TableRow>
          {columns.map((column) => (
            <TableCell key={column.key}>{column.header}</TableCell>
          ))}
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.map((row, rowIndex) => (
          <TableRow key={rowIndex}>
            {columns.map((column) => (
              <TableCell key={column.key}>{column.render(row)}</TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
