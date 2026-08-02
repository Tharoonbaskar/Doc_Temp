import type { PaginatedResult } from './types';

export const normalize = (value: string): string => value.trim().toLowerCase();

export const includesText = (value: string | undefined | null, search: string): boolean => {
  if (!search) {
    return true;
  }
  return normalize(value ?? '').includes(normalize(search));
};

export const paginate = <T>(rows: T[], page: number, pageSize: number): PaginatedResult<T> => {
  const safePage = page < 1 ? 1 : page;
  const safePageSize = pageSize < 1 ? 10 : pageSize;
  const start = (safePage - 1) * safePageSize;
  const end = start + safePageSize;

  return {
    rows: rows.slice(start, end),
    total: rows.length,
    page: safePage,
    pageSize: safePageSize,
  };
};

export const makeCode = (prefix: string, seed: string): string => {
  const token = seed
    .trim()
    .toUpperCase()
    .replace(/[^A-Z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 32);

  const suffix = Date.now().toString().slice(-6);
  return `${prefix}_${token || 'ITEM'}_${suffix}`;
};
