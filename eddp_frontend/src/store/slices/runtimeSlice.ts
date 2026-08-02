import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

import { DEFAULT_PAGE_SIZE, type ListQueryState } from '../../features/shared/types';

type RuntimeState = {
  query: ListQueryState;
  selectedRequestId: string;
  selectedBusinessReference: string;
  selectedCorrelationId: string;
};

const initialState: RuntimeState = {
  query: {
    search: '',
    status: '',
    page: 1,
    pageSize: DEFAULT_PAGE_SIZE,
  },
  selectedRequestId: '',
  selectedBusinessReference: '',
  selectedCorrelationId: '',
};

const runtimeSlice = createSlice({
  name: 'runtime',
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
    setSelectedRequestId(state, action: PayloadAction<string>) {
      state.selectedRequestId = action.payload;
    },
    setSelectedCorrelationId(state, action: PayloadAction<string>) {
      state.selectedCorrelationId = action.payload;
      state.selectedBusinessReference = action.payload;
    },
    setSelectedBusinessReference(state, action: PayloadAction<string>) {
      state.selectedBusinessReference = action.payload;
      state.selectedCorrelationId = action.payload;
    },
    resetFilters(state) {
      state.query = initialState.query;
    },
  },
});

export const {
  setSearch,
  setStatus,
  setPage,
  setPageSize,
  setSelectedRequestId,
  setSelectedCorrelationId,
  setSelectedBusinessReference,
  resetFilters,
} = runtimeSlice.actions;
export const runtimeReducer = runtimeSlice.reducer;
