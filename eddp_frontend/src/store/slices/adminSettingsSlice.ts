import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

type AdminSettingsState = {
  density: 'comfortable' | 'compact';
  enableNotifications: boolean;
};

const initialState: AdminSettingsState = {
  density: 'comfortable',
  enableNotifications: true,
};

const adminSettingsSlice = createSlice({
  name: 'adminSettings',
  initialState,
  reducers: {
    setDensity(state, action: PayloadAction<'comfortable' | 'compact'>) {
      state.density = action.payload;
    },
    setEnableNotifications(state, action: PayloadAction<boolean>) {
      state.enableNotifications = action.payload;
    },
  },
});

export const { setDensity, setEnableNotifications } = adminSettingsSlice.actions;
export const adminSettingsReducer = adminSettingsSlice.reducer;
