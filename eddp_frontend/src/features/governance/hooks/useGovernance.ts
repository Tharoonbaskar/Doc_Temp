import { useQuery } from '@tanstack/react-query';

import { governanceApi } from '../api/governanceApi';

const KEY = ['governance'];

export const useAuditLogs = () =>
  useQuery({
    queryKey: [...KEY, 'audit-logs'],
    queryFn: governanceApi.listAuditLogs,
  });

export const useAuditLog = (id: string) =>
  useQuery({
    queryKey: [...KEY, 'audit-logs', id],
    queryFn: () => governanceApi.getAuditLogById(id),
    enabled: Boolean(id),
  });

export const useActivityLogs = () =>
  useQuery({
    queryKey: [...KEY, 'activity-logs'],
    queryFn: governanceApi.listActivityLogs,
  });

export const useSnapshots = () =>
  useQuery({
    queryKey: [...KEY, 'snapshots'],
    queryFn: governanceApi.listSnapshots,
  });
