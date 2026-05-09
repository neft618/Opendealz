import apiClient from './client';

export const usersApi = {
  getUser: (id) => apiClient.get(`/users/${id}`),
  updateProfile: (data) => apiClient.patch('/users/me/profile', data),
  switchRole: (role) => apiClient.patch('/users/me/role', { role }),
  addPortfolio: (formData) =>
    apiClient.post('/users/me/portfolio', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  deletePortfolio: (id) => apiClient.delete(`/users/me/portfolio/${id}`),
  getReviews: (id, params) => apiClient.get(`/users/${id}/reviews`, { params }),
};
