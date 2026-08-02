import { Stack } from '@mui/material';
import type { ReactNode } from 'react';

import { EmptyState } from '../components/common/EmptyState';
import { PageHeader } from '../components/common/PageHeader';

type Props = {
  title: string;
  subtitle: string;
  icon?: ReactNode;
};

export function FeaturePlaceholderPage({ title, subtitle, icon }: Props) {
  return (
    <Stack spacing={3}>
      <PageHeader title={title} subtitle={subtitle} />
      <EmptyState
        icon={icon}
        title="Module foundation ready"
        description="Business implementation for this module is intentionally deferred after Sprint 10A."
      />
    </Stack>
  );
}
