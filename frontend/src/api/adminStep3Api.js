import api from "./axios.js";

export const adminStep3Api = {
  analyticsOverview: () => api.get("/admin/analytics/overview"),
  analyticsSymptoms: () => api.get("/admin/analytics/symptoms"),
  analyticsSpecialties: () => api.get("/admin/analytics/specialties"),
  analyticsDoctors: () => api.get("/admin/analytics/doctors"),
  analyticsAi: () => api.get("/admin/analytics/ai"),
  analyticsNotifications: () => api.get("/admin/analytics/notifications"),
  reviewCases: (params = {}) => api.get("/admin/review-cases", { params }),
  reviewCase: (caseId) => api.get(`/admin/review-cases/${caseId}`),
  assignReviewCase: (caseId, payload) => api.patch(`/admin/review-cases/${caseId}/assign`, payload),
  updateReviewCaseStatus: (caseId, payload) => api.patch(`/admin/review-cases/${caseId}/status`, payload),
  knowledgeDocuments: () => api.get("/admin/knowledge-base"),
  knowledgeDocument: (id) => api.get(`/admin/knowledge-base/${id}`),
  createKnowledgeDocument: (payload) => api.post("/admin/knowledge-base", payload),
  updateKnowledgeDocument: (id, payload) => api.patch(`/admin/knowledge-base/${id}`, payload),
  deleteKnowledgeDocument: (id) => api.delete(`/admin/knowledge-base/${id}`),
  reindexKnowledgeDocument: (id) => api.post(`/admin/knowledge-base/${id}/reindex`),
  notificationLogs: (params = {}) => api.get("/admin/notification-logs", { params }),
  sendTestNotification: (payload) => api.post("/admin/notifications/test", payload),
};
