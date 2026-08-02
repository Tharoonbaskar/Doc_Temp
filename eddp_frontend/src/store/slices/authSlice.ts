import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

import type { AuthTokens, AuthUser } from '../../types/auth';

type AuthState = {
  isAuthenticated: boolean;
  user: AuthUser | null;
  tokens: AuthTokens | null;
  isInitializing: boolean;
};

const initialState: AuthState = {
  isAuthenticated: false,
  user: null,
  tokens: null,
  isInitializing: true,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setSession(state, action: PayloadAction<{ user: AuthUser; tokens: AuthTokens }>) {
      state.isAuthenticated = true;
      state.user = action.payload.user;
      state.tokens = action.payload.tokens;
      state.isInitializing = false;
    },
    clearSession(state) {
      state.isAuthenticated = false;
      state.user = null;
      state.tokens = null;
      state.isInitializing = false;
    },
    finishInitialization(state) {
      state.isInitializing = false;
    },
  },
});

export const { setSession, clearSession, finishInitialization } = authSlice.actions;

export const authReducer = authSlice.reducer;
