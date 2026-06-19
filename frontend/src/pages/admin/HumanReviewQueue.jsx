import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { adminStep3Api } from "../../api/adminStep3Api.js";
import { getApiError } from "../../api/axios.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import Select from "../../components/Select.jsx";
import Table from "../../components/Table.jsx";
import UrgencyBadge from "../../components/UrgencyBadge.jsx";
import { formatDateTime } from "../../utils/format.js";

export default function HumanReviewQueue() {
  const [cases, setCases] = useState([]);
  const [filters, setFilters] = useState({ status: "", risk_level: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
        const { data } = await adminStep3Api.reviewCases(params);
        setCases(data);
      } catch (err) {
        setError(getApiError(err));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [filters]);

  return (
    <Card>
      <CardHeader
        title="Human Review Queue"
        description="Risky or low-confidence triage sessions awaiting admin review."
        action={
          <div className="grid gap-2 sm:grid-cols-2">
            <Select value={filters.status} onChange={(event) => setFilters((current) => ({ ...current, status: event.target.value }))}>
              <option value="">All status</option>
              <option value="pending">Pending</option>
              <option value="in_review">In review</option>
              <option value="resolved">Resolved</option>
              <option value="dismissed">Dismissed</option>
            </Select>
            <Select value={filters.risk_level} onChange={(event) => setFilters((current) => ({ ...current, risk_level: event.target.value }))}>
              <option value="">All risk</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </Select>
          </div>
        }
      />
      <CardBody>
        {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        {loading ? (
          <Loader label="Loading review cases" />
        ) : cases.length === 0 ? (
          <EmptyState title="No review cases found" />
        ) : (
          <Table
            columns={["Patient", "Urgency", "Risk", "Status", "Confidence", "Reason", "Created", "Action"]}
            rows={cases}
            renderRow={(item) => (
              <tr key={item.id}>
                <td className="px-4 py-3 font-medium text-gray-950">{item.patient_name}</td>
                <td className="px-4 py-3"><UrgencyBadge level={item.urgency_level} /></td>
                <td className="px-4 py-3"><Badge tone={item.risk_level}>{item.risk_level}</Badge></td>
                <td className="px-4 py-3"><Badge tone={item.status}>{item.status}</Badge></td>
                <td className="px-4 py-3 text-gray-600">{item.ai_confidence ? `${Math.round(item.ai_confidence * 100)}%` : "N/A"}</td>
                <td className="max-w-sm px-4 py-3 text-gray-600">{item.reason}</td>
                <td className="px-4 py-3 text-gray-600">{formatDateTime(item.created_at)}</td>
                <td className="px-4 py-3">
                  <Link to={`/admin/review-cases/${item.id}`}>
                    <Button variant="secondary">Review</Button>
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
