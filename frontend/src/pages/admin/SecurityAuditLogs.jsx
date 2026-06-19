import { useEffect, useState } from "react";

import { getApiError } from "../../api/axios.js";
import { securityApi } from "../../api/securityApi.js";
import Badge from "../../components/Badge.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Input from "../../components/Input.jsx";
import Loader from "../../components/Loader.jsx";
import Table from "../../components/Table.jsx";
import { formatDateTime } from "../../utils/format.js";

export default function SecurityAuditLogs() {
  const [logs, setLogs] = useState([]);
  const [filters, setFilters] = useState({ action: "", user_id: "", resource_type: "", ip_address: "", date: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
        const { data } = await securityApi.auditLogs(params);
        setLogs(data);
      } catch (err) {
        setError(getApiError(err));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [filters]);

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  return (
    <Card>
      <CardHeader
        title="Security Audit Logs"
        description="Access, auth, appointment, triage, and admin patient-data events."
        action={
          <div className="grid gap-2 sm:grid-cols-5">
            <Input label="Action" value={filters.action} onChange={(event) => updateFilter("action", event.target.value)} />
            <Input label="User ID" value={filters.user_id} onChange={(event) => updateFilter("user_id", event.target.value)} />
            <Input label="Resource" value={filters.resource_type} onChange={(event) => updateFilter("resource_type", event.target.value)} />
            <Input label="IP" value={filters.ip_address} onChange={(event) => updateFilter("ip_address", event.target.value)} />
            <input
              type="date"
              value={filters.date}
              onChange={(event) => updateFilter("date", event.target.value)}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
            />
          </div>
        }
      />
      <CardBody>
        {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        {loading ? (
          <Loader label="Loading security logs" />
        ) : logs.length === 0 ? (
          <EmptyState title="No security audit logs found" />
        ) : (
          <Table
            columns={["Time", "User", "Action", "Resource", "IP", "Suspicious", "Metadata"]}
            rows={logs}
            renderRow={(log) => (
              <tr key={log.id}>
                <td className="px-4 py-3 text-gray-600">{formatDateTime(log.created_at)}</td>
                <td className="px-4 py-3 text-gray-600">{log.user_name || log.user_id || "System"}</td>
                <td className="px-4 py-3 font-medium text-gray-950">{log.action}</td>
                <td className="px-4 py-3 text-gray-600">{log.resource_type}{log.resource_id ? ` #${log.resource_id}` : ""}</td>
                <td className="px-4 py-3 text-gray-600">{log.ip_address || "Unknown"}</td>
                <td className="px-4 py-3">{log.suspicious ? <Badge tone="urgent">Suspicious</Badge> : <Badge>Normal</Badge>}</td>
                <td className="max-w-sm px-4 py-3">
                  <pre className="max-h-32 overflow-auto rounded bg-gray-50 p-2 text-xs text-gray-700">{JSON.stringify(log.metadata, null, 2)}</pre>
                </td>
              </tr>
            )}
          />
        )}
      </CardBody>
    </Card>
  );
}
