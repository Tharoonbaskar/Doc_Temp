import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

type AppState = {
  sidebarOpen: boolean;
};

const initialState: AppState = {
  sidebarOpen: true,
};

const appSlice = createSlice({
  name: 'app',
  initialState,
  reducers: {
    setSidebarOpen(state, action: PayloadAction<boolean>) {
      state.sidebarOpen = action.payload;
    },
    toggleSidebar(state) {
      state.sidebarOpen = !state.sidebarOpen;
    },
  },
});

export const { setSidebarOpen, toggleSidebar } = appSlice.actions;

export const appReducer = appSlice.reducer;
