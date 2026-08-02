import { Box, Paper, Typography } from '@mui/material';
import type { ReactNode } from 'react';

type Props = {
  title: string;
  description?: string;
  icon?: ReactNode;
};

export function EmptyState({ title, description, icon }: Props) {
  return (
    <Paper variant="outlined" sx={{ p: 4, textAlign: 'center' }}>
      {icon ? <Box sx={{ mb: 1 }}>{icon}</Box> : null}
      <Typography variant="subtitle1">{title}</Typography>
      {description ? (
        <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
          {description}
        </Typography>
      ) : null}
    </Paper>
  );
}
