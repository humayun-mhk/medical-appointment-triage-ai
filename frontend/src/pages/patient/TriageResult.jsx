import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getApiError } from "../../api/axios.js";
import { triageApi } from "../../api/triageApi.js";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import RedFlagAlert from "../../components/RedFlagAlert.jsx";
import SafetyDisclaimer from "../../components/SafetyDisclaimer.jsx";
import UrgencyBadge from "../../components/UrgencyBadge.jsx";

export default function TriageResult() {
  const { sessionId } = useParams();
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    triageApi
      .getResult(sessionId)
      .then(({ data }) => setResult(data))
      .catch((err) => setError(getApiError(err)))
      .finally(() => setLoading(false));
  }, [sessionId]);

  if (loading) return <Loader label="Loading triage result" />;
  if (!result) return <EmptyState title="Triage result not found" message={error} />;

  const symptoms = result.structured_symptoms || {};

  return (
    <div className="space-y-6">
      <SafetyDisclaimer compact />
      <RedFlagAlert show={result.red_flag_status || result.urgency_level === "emergency"} message={result.safety_message} />
      {error && <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
      <Card>
        <CardHeader title="Triage Result" action={<UrgencyBadge level={result.urgency_level} />} />
        <CardBody className="space-y-5">
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-md bg-gray-50 p-4">
              <p className="text-sm text-gray-500">Main symptoms</p>
              <p className="mt-1 font-semibold text-gray-950">{(symptoms.main_symptoms || []).join(", ") || "Not extracted"}</p>
            </div>
            <div className="rounded-md bg-gray-50 p-4">
              <p className="text-sm text-gray-500">Duration</p>
              <p className="mt-1 font-semibold text-gray-950">{symptoms.duration || "Not specified"}</p>
            </div>
            <div className="rounded-md bg-gray-50 p-4">
              <p className="text-sm text-gray-500">Severity</p>
              <p className="mt-1 font-semibold text-gray-950">{symptoms.severity ? `${symptoms.severity}/10` : "Not specified"}</p>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-sm font-medium text-gray-500">Recommended specialty</p>
              <p className="mt-1 text-lg font-semibold text-gray-950">{result.recommended_specialty?.name || "General Physician"}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500">Secondary specialty</p>
              <p className="mt-1 text-lg font-semibold text-gray-950">{result.secondary_specialty?.name || "None"}</p>
            </div>
          </div>
          <div className="rounded-md border border-gray-200 p-4">
            <p className="text-sm font-medium text-gray-500">Routing reason</p>
            <p className="mt-1 text-sm leading-6 text-gray-700">{result.ai_reason || "No reason available."}</p>
            <p className="mt-2 text-sm text-gray-500">Confidence: {Math.round((result.ai_confidence || 0) * 100)}%</p>
          </div>
          <div className="rounded-md border border-teal-200 bg-teal-50 p-4">
            <p className="text-sm font-semibold text-teal-900">Doctor summary preview</p>
            <p className="mt-1 text-sm leading-6 text-teal-900">{result.doctor_summary}</p>
          </div>
          <Link to={`/patient/triage/${sessionId}/doctors`}>
            <Button>View Recommended Doctors</Button>
          </Link>
        </CardBody>
      </Card>
    </div>
  );
}
