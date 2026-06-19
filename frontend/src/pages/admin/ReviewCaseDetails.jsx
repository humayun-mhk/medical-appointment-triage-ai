import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { adminStep3Api } from "../../api/adminStep3Api.js";
import { getApiError } from "../../api/axios.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import Loader from "../../components/Loader.jsx";
import Select from "../../components/Select.jsx";
import UrgencyBadge from "../../components/UrgencyBadge.jsx";
import { useAuth } from "../../hooks/useAuth.js";
import { formatDateTime } from "../../utils/format.js";

export default function ReviewCaseDetails() {
  const { caseId } = useParams();
  const { user } = useAuth();
  const [reviewCase, setReviewCase] = useState(null);
  const [statusValue, setStatusValue] = useState("resolved");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const { data } = await adminStep3Api.reviewCase(caseId);
      setReviewCase(data);
      setNotes(data.review_notes || "");
      setStatusValue(data.status === "pending" ? "resolved" : data.status);
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [caseId]);

  async function assignToMe() {
    setSaving(true);
    setError("");
    try {
      const { data } = await adminStep3Api.assignReviewCase(caseId, { assigned_admin_id: user?.id });
      setReviewCase(data);
      setSuccess("Case assigned.");
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setSaving(false);
    }
  }

  async function updateStatus(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const { data } = await adminStep3Api.updateReviewCaseStatus(caseId, { status: statusValue, review_notes: notes });
      setReviewCase(data);
      setSuccess("Review status updated.");
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <Loader label="Loading review case" />;
  if (!reviewCase) return <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error || "Review case not found"}</div>;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader
          title={`Review Case #${reviewCase.id}`}
          description={`Created ${formatDateTime(reviewCase.created_at)}`}
          action={<Button variant="secondary" onClick={assignToMe} disabled={saving}>Assign to me</Button>}
        />
        <CardBody className="space-y-4">
          {error && <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
          {success && <div className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{success}</div>}
          <div className="grid gap-4 md:grid-cols-4">
            <div>
              <p className="text-sm text-gray-500">Patient</p>
              <p className="font-semibold text-gray-950">{reviewCase.patient_name}</p>
            </div>
            <div>
              <p className="text-sm text-gray-500">Urgency</p>
              <UrgencyBadge level={reviewCase.urgency_level} />
            </div>
            <div>
              <p className="text-sm text-gray-500">Risk</p>
              <Badge tone={reviewCase.risk_level}>{reviewCase.risk_level}</Badge>
            </div>
            <div>
              <p className="text-sm text-gray-500">Status</p>
              <Badge tone={reviewCase.status}>{reviewCase.status}</Badge>
            </div>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Review reason</p>
            <p className="mt-1 text-gray-700">{reviewCase.reason}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Raw symptoms</p>
            <p className="mt-1 rounded-md bg-gray-50 p-3 text-sm text-gray-700">{reviewCase.raw_input}</p>
          </div>
          <div>
            <p className="text-sm font-medium text-gray-500">Structured symptoms</p>
            <pre className="mt-1 overflow-auto rounded-md bg-gray-950 p-3 text-xs text-gray-50">{JSON.stringify(reviewCase.structured_symptoms, null, 2)}</pre>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Resolve Review" />
        <CardBody>
          <form onSubmit={updateStatus} className="space-y-4">
            <Select value={statusValue} onChange={(event) => setStatusValue(event.target.value)}>
              <option value="in_review">In review</option>
              <option value="resolved">Resolved</option>
              <option value="dismissed">Dismissed</option>
            </Select>
            <textarea
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              className="min-h-32 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
              placeholder="Review notes"
            />
            <Button type="submit" disabled={saving}>{saving ? "Saving..." : "Update Review"}</Button>
          </form>
        </CardBody>
      </Card>
    </div>
  );
}
