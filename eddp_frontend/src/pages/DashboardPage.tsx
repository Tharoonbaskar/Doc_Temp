import { Box, Stack } from '@mui/material';

import { AppCard } from '../components/common/AppCard';
import { PageHeader } from '../components/common/PageHeader';

const dashboardCards = [
  { title: 'Documents', value: 0 },
  { title: 'Templates', value: 0 },
  { title: 'Generated Documents', value: 0 },
  { title: 'Users', value: 0 },
  { title: 'Runtime Queue', value: 0 },
  { title: 'Audit Logs', value: 0 },
] as const;

export function DashboardPage() {
  return (
    <Stack spacing={3}>
      <PageHeader
        title="Enterprise Dashboard"
        subtitle="Operational overview for EDDP platform modules."
      />
      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: {
            xs: '1fr',
            sm: 'repeat(2, minmax(0, 1fr))',
            lg: 'repeat(3, minmax(0, 1fr))',
          },
        }}
      >
        {dashboardCards.map((card) => (
          <Box key={card.title}>
            <AppCard title={card.title} value={card.value} />
          </Box>
        ))}
      </Box>
    </Stack>
  );
}
