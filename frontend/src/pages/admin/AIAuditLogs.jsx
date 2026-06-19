import { useEffect, useState } from "react";

import { getApiError } from "../../api/axios.js";
import { triageApi } from "../../api/triageApi.js";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Input from "../../components/Input.jsx";
import Loader from "../../components/Loader.jsx";
import Table from "../../components/Table.jsx";
import { formatDateTime } from "../../utils/format.js";

export default function AIAuditLogs() {
  const [logs, setLogs] = useState([]);
  const [filters, setFilters] = useState({ agent_name: "", session_id: "", model_name: "", date: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
        const { data } = await triageApi.adminAuditLogs(params);
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
        title="AI Audit Logs"
        action={
          <div className="grid gap-2 md:grid-cols-4">
            <Input placeholder="Agent" value={filters.agent_name} onChange={(event) => updateFilter("agent_name", event.target.value)} />
            <Input placeholder="Session ID" value={filters.session_id} onChange={(event) => updateFilter("session_id", event.target.value)} />
            <Input placeholder="Model" value={filters.model_name} onChange={(event) => updateFilter("model_name", event.target.value)} />
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
          <Loader label="Loading audit logs" />
        ) : logs.length === 0 ? (
          <EmptyState title="No audit logs found" />
        ) : (
          <Table
            columns={["Session", "Agent", "Model", "Safety Flags", "Created", "Payload"]}
            rows={logs}
            renderRow={(log) => (
              <tr key={log.id} className="align-top">
                <td className="px-4 py-3 font-medium text-gray-950">#{log.session_id}</td>
                <td className="px-4 py-3 text-gray-600">{log.agent_name}</td>
                <td className="px-4 py-3 text-gray-600">{log.model_name || "N/A"}</td>
                <td className="px-4 py-3">
                  <pre className="max-w-xs overflow-x-auto rounded bg-gray-100 p-2 text-xs">{JSON.stringify(log.safety_flags, null, 2)}</pre>
                </td>
                <td className="px-4 py-3 text-gray-600">{formatDateTime(log.created_at)}</td>
                <td className="px-4 py-3">
                  <pre className="max-w-md overflow-x-auto rounded bg-gray-950 p-2 text-xs text-gray-100">{JSON.stringify(log.output_payload, null, 2)}</pre>
                </td>
              </tr>
            )}
          />
        )}
      </CardBody>
    </Card>
  );
}
