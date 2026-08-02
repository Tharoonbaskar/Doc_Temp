import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

import { DEFAULT_PAGE_SIZE, type ListQueryState } from '../../features/shared/types';

type RulesState = {
  query: ListQueryState;
};

const initialState: RulesState = {
  query: {
    search: '',
    status: '',
    page: 1,
    pageSize: DEFAULT_PAGE_SIZE,
  },
};

const rulesSlice = createSlice({
  name: 'rules',
  initialState,
  reducers: {
    setSearch(state, action: PayloadAction<string>) {
      state.query.search = action.payload;
      state.query.page = 1;
    },
    setStatus(state, action: PayloadAction<ListQueryState['status']>) {
      state.query.status = action.payload;
      state.query.page = 1;
    },
    setPage(state, action: PayloadAction<number>) {
      state.query.page = action.payload;
    },
    setPageSize(state, action: PayloadAction<number>) {
      state.query.pageSize = action.payload;
      state.query.page = 1;
    },
    resetFilters(state) {
      state.query = initialState.query;
    },
  },
});

export const { setSearch, setStatus, setPage, setPageSize, resetFilters } = rulesSlice.actions;
export const rulesReducer = rulesSlice.reducer;
