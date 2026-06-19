import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { getApiError } from "../../api/axios.js";
import { triageApi } from "../../api/triageApi.js";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import SafetyDisclaimer from "../../components/SafetyDisclaimer.jsx";

export default function SymptomTriage() {
  const [rawInput, setRawInput] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const { data } = await triageApi.analyze(rawInput);
      navigate(`/patient/triage/${data.session_id}/result`);
    } catch (err) {
      setError(getApiError(err, "Unable to analyze symptoms"));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <SafetyDisclaimer />
      <Card>
        <CardHeader title="Symptom Triage" description="Describe your symptoms and we will route you to a suitable specialty." />
        <CardBody>
          {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
          <form className="space-y-4" onSubmit={handleSubmit}>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-gray-700">Symptoms</span>
              <textarea
                value={rawInput}
                onChange={(event) => setRawInput(event.target.value)}
                maxLength={3000}
                required
                placeholder="Example: I have fever, sore throat, and cough for 3 days."
                className="min-h-48 w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
              />
            </label>
            <div className="flex items-center justify-between gap-3">
              <p className="text-xs text-gray-500">{rawInput.length}/3000</p>
              <Button type="submit" isLoading={loading}>
                Analyze Symptoms
              </Button>
            </div>
          </form>
        </CardBody>
      </Card>
    </div>
  );
}
