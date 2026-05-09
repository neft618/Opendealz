import apiClient from './client';

export const disputesApi = {
  create: (data) => apiClient.post('/disputes', data),
  get: (id) => apiClient.get(`/disputes/${id}`),
  addMessage: (id, content, file) => {
    if (file) {
      const formData = new FormData();
      formData.append('content', content);
      formData.append('file', file);
      return apiClient.post(`/disputes/${id}/messages`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
    }
    return apiClient.post(`/disputes/${id}/messages?content=${encodeURIComponent(content)}`);
  },
  updateStatus: (id, status) => apiClient.patch(`/disputes/${id}/status`, { status }),
  resolve: (id, data) => apiClient.post(`/disputes/${id}/resolve`, data),
};
