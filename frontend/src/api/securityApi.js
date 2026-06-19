import api from "./axios.js";

export const securityApi = {
  auditLogs: (params = {}) => api.get("/admin/security-audit-logs", { params }),
};
