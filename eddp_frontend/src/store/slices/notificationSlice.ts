import { createSlice, type PayloadAction } from '@reduxjs/toolkit';

export type NotificationSeverity = 'success' | 'info' | 'warning' | 'error';

export type AppNotification = {
  id: string;
  message: string;
  severity: NotificationSeverity;
};

type NotificationState = {
  queue: AppNotification[];
};

const initialState: NotificationState = {
  queue: [],
};

const notificationSlice = createSlice({
  name: 'notification',
  initialState,
  reducers: {
    enqueueNotification(state, action: PayloadAction<Omit<AppNotification, 'id'> & { id?: string }>) {
      const id = action.payload.id ?? crypto.randomUUID();
      state.queue.push({
        id,
        message: action.payload.message,
        severity: action.payload.severity,
      });
    },
    dequeueNotification(state, action: PayloadAction<string>) {
      state.queue = state.queue.filter((item) => item.id !== action.payload);
    },
    clearNotifications(state) {
      state.queue = [];
    },
  },
});

export const { enqueueNotification, dequeueNotification, clearNotifications } = notificationSlice.actions;
export const notificationReducer = notificationSlice.reducer;
