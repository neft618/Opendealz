import { create } from 'zustand';
import { notificationsApi } from '../api/notifications';

export const useNotificationStore = create((set, get) => ({
  unreadCount: 0,
  pollingInterval: null,

  fetchUnreadCount: async () => {
    try {
      const { data } = await notificationsApi.unreadCount();
      set({ unreadCount: data.count });
    } catch {
      // ignore
    }
  },

  startPolling: () => {
    if (get().pollingInterval) return;
    get().fetchUnreadCount();
    const interval = setInterval(() => {
      get().fetchUnreadCount();
    }, 30000);
    set({ pollingInterval: interval });
  },

  stopPolling: () => {
    const { pollingInterval } = get();
    if (pollingInterval) {
      clearInterval(pollingInterval);
      set({ pollingInterval: null });
    }
  },

  decrementUnread: () =>
    set((state) => ({ unreadCount: Math.max(0, state.unreadCount - 1) })),

  resetUnread: () => set({ unreadCount: 0 }),
}));
