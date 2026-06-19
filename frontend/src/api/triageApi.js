import api from "./axios.js";

export const triageApi = {
  analyze: (raw_input) => api.post("/triage/analyze", { raw_input }),
  analyzeSession: (session_id) => api.post("/triage/analyze", { session_id }),
  getResult: (sessionId) => api.get(`/triage/result/${sessionId}`),
  getRecommendedDoctors: (sessionId) => api.get(`/doctors/recommended/${sessionId}`),
  bookFromTriage: (payload) => api.post("/appointments/book-from-triage", payload),
  adminSessions: (params) => api.get("/admin/triage/sessions", { params }),
  adminSessionDetail: (sessionId) => api.get(`/admin/triage/sessions/${sessionId}`),
  adminAuditLogs: (params) => api.get("/admin/ai-audit-logs", { params }),
};
