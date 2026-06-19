import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { getApiError } from "../../api/axios.js";
import { triageApi } from "../../api/triageApi.js";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import Select from "../../components/Select.jsx";
import Table from "../../components/Table.jsx";
import UrgencyBadge from "../../components/UrgencyBadge.jsx";
import { formatDateTime } from "../../utils/format.js";

export default function AdminTriageSessions() {
  const [sessions, setSessions] = useState([]);
  const [filters, setFilters] = useState({ urgency_level: "", red_flag_status: "", date: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value !== ""));
        const { data } = await triageApi.adminSessions(params);
        setSessions(data);
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
        title="AI Triage Sessions"
        action={
          <div className="grid gap-2 sm:grid-cols-3">
            <Select value={filters.urgency_level} onChange={(event) => updateFilter("urgency_level", event.target.value)}>
              <option value="">All urgency</option>
              <option value="routine">Routine</option>
              <option value="soon">Soon</option>
              <option value="urgent">Urgent</option>
              <option value="emergency">Emergency</option>
            </Select>
            <Select value={filters.red_flag_status} onChange={(event) => updateFilter("red_flag_status", event.target.value)}>
              <option value="">All red flags</option>
              <option value="true">Red flag yes</option>
              <option value="false">Red flag no</option>
            </Select>
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
          <Loader label="Loading triage sessions" />
        ) : sessions.length === 0 ? (
          <EmptyState title="No triage sessions found" />
        ) : (
          <Table
            columns={["Patient", "Input Preview", "Urgency", "Red Flag", "Specialty", "Confidence", "Created", "Action"]}
            rows={sessions}
            renderRow={(session) => (
              <tr key={session.session_id}>
                <td className="px-4 py-3 font-medium text-gray-950">{session.patient_name}</td>
                <td className="max-w-xs px-4 py-3 text-gray-600">{session.raw_input_preview}</td>
                <td className="px-4 py-3"><UrgencyBadge level={session.urgency_level} /></td>
                <td className="px-4 py-3 text-gray-600">{session.red_flag_status ? "Yes" : "No"}</td>
                <td className="px-4 py-3 text-gray-600">{session.recommended_specialty || "None"}</td>
                <td className="px-4 py-3 text-gray-600">{session.ai_confidence ? `${Math.round(session.ai_confidence * 100)}%` : "N/A"}</td>
                <td className="px-4 py-3 text-gray-600">{formatDateTime(session.created_at)}</td>
                <td className="px-4 py-3">
                  <Link to={`/admin/triage-sessions/${session.session_id}`}>
                    <Button variant="secondary">View</Button>
                  </Link>
                </td>
              </tr>
            )}
          />
        )}
      </CardBody>
    </Card>
  );
}
