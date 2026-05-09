import { useAuthStore } from '../store/authStore';

export function useAuth() {
  const { user, accessToken, isAuthenticated, activeRole, login, logout, setUser, switchRole } =
    useAuthStore();

  return { user, accessToken, isAuthenticated, activeRole, login, logout, setUser, switchRole };
}
