import { Card, CardContent, Typography } from '@mui/material';
import type { ReactNode } from 'react';

type Props = {
  title: string;
  value?: string | number;
  children?: ReactNode;
};

export function AppCard({ title, value, children }: Props) {
  return (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1 }}>
          {title}
        </Typography>
        {value !== undefined ? (
          <Typography variant="h5" sx={{ fontWeight: 700 }}>
            {value}
          </Typography>
        ) : null}
        {children}
      </CardContent>
    </Card>
  );
}
