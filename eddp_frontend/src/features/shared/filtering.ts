import type { EntityStatus, ListQueryState, PaginatedResult } from './types';
import { includesText, paginate } from './utils';

export const applyListQuery = <T, TStatus = EntityStatus>(
  rows: T[],
  query: ListQueryState,
  options: {
    statusSelector: (row: T) => TStatus;
    searchSelector: (row: T) => string[];
  },
): PaginatedResult<T> => {
  const filtered = rows.filter((row) => {
    const statusPass = !query.status || options.statusSelector(row) === (query.status as unknown as TStatus);
    if (!statusPass) {
      return false;
    }

    const search = query.search.trim();
    if (!search) {
      return true;
    }

    return options.searchSelector(row).some((field) => includesText(field, search));
  });

  return paginate(filtered, query.page, query.pageSize);
};
