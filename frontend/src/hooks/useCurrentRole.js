import { useAuthStore } from '../store/authStore';
import { usersApi } from '../api/users';
import toast from 'react-hot-toast';

export function useCurrentRole() {
  const { activeRole, switchRole, setUser } = useAuthStore();

  const handleSwitchRole = async (role) => {
    try {
      await usersApi.switchRole(role);
      switchRole(role);
      toast.success(`Switched to ${role} mode`);
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to switch role');
    }
  };

  return { activeRole, switchRole: handleSwitchRole };
}
