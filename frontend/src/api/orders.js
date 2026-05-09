import apiClient from './client';

export const ordersApi = {
  list: (params) => apiClient.get('/orders', { params }),
  get: (id) => apiClient.get(`/orders/${id}`),
  create: (data) => apiClient.post('/orders', data),
  update: (id, data) => apiClient.patch(`/orders/${id}`, data),
  delete: (id) => apiClient.delete(`/orders/${id}`),
  applyToOrder: (orderId, data) => apiClient.post(`/orders/${orderId}/applications`, data),
  getApplications: (orderId) => apiClient.get(`/orders/${orderId}/applications`),
  acceptApplication: (orderId, appId) =>
    apiClient.post(`/orders/${orderId}/applications/${appId}/accept`),
};
