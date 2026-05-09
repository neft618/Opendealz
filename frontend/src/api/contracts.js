import apiClient from './client';

export const contractsApi = {
  get: (id) => apiClient.get(`/contracts/${id}`),
  update: (id, data) => apiClient.patch(`/contracts/${id}`, data),
  updateClauses: (id, clauses) => apiClient.patch(`/contracts/${id}/clauses`, clauses),
  sign: (id) => apiClient.post(`/contracts/${id}/sign`),
  addMilestone: (id, data) => apiClient.post(`/contracts/${id}/milestones`, data),
  updateMilestone: (id, mid, data) => apiClient.patch(`/contracts/${id}/milestones/${mid}`, data),
  uploadDeliverable: (id, formData) =>
    apiClient.post(`/contracts/${id}/deliverables`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  downloadDeliverable: (id, did) => apiClient.get(`/contracts/${id}/deliverables/${did}/download`),
  accept: (id) => apiClient.post(`/contracts/${id}/accept`),
  reject: (id) => apiClient.post(`/contracts/${id}/reject`),
  createReview: (id, data) => apiClient.post(`/contracts/${id}/reviews`, data),
};
