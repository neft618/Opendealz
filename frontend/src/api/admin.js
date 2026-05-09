import apiClient from './client';

export const adminApi = {
  getUsers: (params) => apiClient.get('/admin/users', { params }),
  verifyUser: (id) => apiClient.patch(`/admin/users/${id}/verify`),
  deactivateUser: (id) => apiClient.patch(`/admin/users/${id}/deactivate`),
  getMetrics: () => apiClient.get('/admin/metrics'),
  getAuditLog: (params) => apiClient.get('/admin/audit-log', { params }),
  getContracts: (params) => apiClient.get('/admin/contracts', { params }),
  getDisputes: (params) => apiClient.get('/admin/disputes', { params }),
};
