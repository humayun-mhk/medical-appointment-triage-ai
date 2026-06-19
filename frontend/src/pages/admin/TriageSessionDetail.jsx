import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";

import { getApiError } from "../../api/axios.js";
import { triageApi } from "../../api/triageApi.js";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import RedFlagAlert from "../../components/RedFlagAlert.jsx";
import UrgencyBadge from "../../components/UrgencyBadge.jsx";
import { formatDateTime } from "../../utils/format.js";

function JsonBlock({ title, data }) {
  return (
    <div>
      <p className="mb-2 text-sm font-semibold text-gray-800">{title}</p>
      <pre className="overflow-x-auto rounded-md bg-gray-950 p-3 text-xs text-gray-100">
        {JSON.stringify(data || {}, null, 2)}
      </pre>
    </div>
  );
}

export default function AdminTriageSessionDetail() {
  const { sessionId } = useParams();
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    triageApi
      .adminSessionDetail(sessionId)
      .then(({ data }) => setSession(data))
      .catch((err) => setError(getApiError(err)))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) return <Loader label="Loading triage session" />;
  if (!session) return <EmptyState title="Triage session not found" message={error} />;

  return (
    <div className="space-y-6">
      <RedFlagAlert show={session.red_flag_status} message={session.safety_message} />
      <Card>
        <CardHeader title={`Triage Session #${session.session_id}`} action={<UrgencyBadge level={session.urgency_level} />} />
        <CardBody className="space-y-4">
          <div className="grid gap-4 md:grid-cols-3">
            <p className="text-sm text-gray-600"><span className="font-semibold text-gray-800">Patient:</span> {session.patient_name}</p>
            <p className="text-sm text-gray-600"><span className="font-semibold text-gray-800">Created:</span> {formatDateTime(session.created_at)}</p>
            <p className="text-sm text-gray-600"><span className="font-semibold text-gray-800">Confidence:</span> {session.ai_confidence ? `${Math.round(session.ai_confidence * 100)}%` : "N/A"}</p>
          </div>
          <div className="rounded-md border border-gray-200 p-4">
            <p className="text-sm font-semibold text-gray-800">Raw input</p>
            <p className="mt-1 text-sm leading-6 text-gray-700">{session.raw_input}</p>
          </div>
          <div className="rounded-md border border-teal-200 bg-teal-50 p-4">
            <p className="text-sm font-semibold text-teal-900">Doctor summary</p>
            <p className="mt-1 text-sm leading-6 text-teal-900">{session.doctor_summary}</p>
          </div>
          <JsonBlock title="Structured symptoms" data={session.structured_symptoms} />
          <JsonBlock title="Audit logs" data={session.audit_logs} />
        </CardBody>
      </Card>
    </div>
  );
}
