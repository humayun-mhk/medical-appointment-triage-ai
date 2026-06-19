import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useParams } from "react-router-dom";

import api, { getApiError } from "../../api/axios.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import RedFlagAlert from "../../components/RedFlagAlert.jsx";
import SafetyDisclaimer from "../../components/SafetyDisclaimer.jsx";
import UrgencyBadge from "../../components/UrgencyBadge.jsx";
import { doctorNotesSchema } from "../../schemas/doctor.js";
import { formatDate, formatDateTime } from "../../utils/format.js";

export default function DoctorAppointmentDetails() {
  const { appointmentId } = useParams();
  const [appointment, setAppointment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [statusBusy, setStatusBusy] = useState("");
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(doctorNotesSchema),
    defaultValues: { doctor_notes: "" },
  });

  async function load() {
    try {
      const { data } = await api.get(`/doctor/appointments/${appointmentId}`);
      setAppointment(data);
      reset({ doctor_notes: data.doctor_notes || "" });
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [appointmentId]);

  async function saveNotes(values) {
    setError("");
    setMessage("");
    try {
      const { data } = await api.post(`/doctor/appointments/${appointmentId}/notes`, values);
      setAppointment(data);
      setMessage("Doctor notes saved.");
    } catch (err) {
      setError(getApiError(err, "Unable to save notes"));
    }
  }

  async function updateStatus(status) {
    setStatusBusy(status);
    setError("");
    setMessage("");
    try {
      const { data } = await api.post(`/doctor/appointments/${appointmentId}/status`, { status });
      setAppointment(data);
      setMessage("Appointment status updated.");
    } catch (err) {
      setError(getApiError(err, "Unable to update status"));
    } finally {
      setStatusBusy("");
    }
  }

  if (loading) return <Loader label="Loading appointment" />;
  if (!appointment) return <EmptyState title="Appointment not found" message={error} />;

  return (
    <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <Card>
        <CardHeader title="Appointment Details" action={<Badge>{appointment.status}</Badge>} />
        <CardBody className="space-y-3 text-sm text-gray-600">
          {error && <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
          {message && <div className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</div>}
          <p><span className="font-semibold text-gray-800">Patient:</span> {appointment.patient?.full_name}</p>
          <p><span className="font-semibold text-gray-800">Email:</span> {appointment.patient?.email}</p>
          <p><span className="font-semibold text-gray-800">Date of birth:</span> {formatDate(appointment.patient?.date_of_birth)}</p>
          <p><span className="font-semibold text-gray-800">Phone:</span> {appointment.patient?.phone || "Not set"}</p>
          <p><span className="font-semibold text-gray-800">Gender:</span> {appointment.patient?.gender || "Not set"}</p>
          <p><span className="font-semibold text-gray-800">Blood group:</span> {appointment.patient?.blood_group || "Not set"}</p>
          <p><span className="font-semibold text-gray-800">Allergies:</span> {appointment.patient?.allergies || "None"}</p>
          <p><span className="font-semibold text-gray-800">Chronic conditions:</span> {appointment.patient?.chronic_conditions || "None"}</p>
          <p><span className="font-semibold text-gray-800">Appointment:</span> {formatDateTime(appointment.slot_start_time)}</p>
          <p><span className="font-semibold text-gray-800">Symptoms:</span> {appointment.symptoms || "None"}</p>
          <p><span className="font-semibold text-gray-800">Patient notes:</span> {appointment.patient_notes || "None"}</p>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="Doctor Actions" />
        <CardBody className="space-y-5">
          <form className="space-y-3" onSubmit={handleSubmit(saveNotes)}>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-gray-700">Doctor notes</span>
              <textarea className="min-h-40 w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100" {...register("doctor_notes")} />
              {errors.doctor_notes && <span className="mt-1 block text-sm text-rose-600">{errors.doctor_notes.message}</span>}
            </label>
            <Button type="submit" isLoading={isSubmitting}>
              Save Notes
            </Button>
          </form>

          <div className="flex flex-wrap gap-3 border-t border-gray-100 pt-5">
            {["completed", "no_show", "cancelled"].map((status) => (
              <Button
                key={status}
                variant={status === "cancelled" ? "danger" : "secondary"}
                isLoading={statusBusy === status}
                onClick={() => updateStatus(status)}
              >
                Mark {status.replace("_", " ")}
              </Button>
            ))}
          </div>
        </CardBody>
      </Card>

      {appointment.triage_session_id && (
        <Card className="lg:col-span-2">
          <CardHeader
            title="AI Triage Summary"
            description="Routing support only. Final medical judgment belongs to the doctor."
            action={<UrgencyBadge level={appointment.urgency_level} />}
          />
          <CardBody className="space-y-4">
            <SafetyDisclaimer compact />
            <RedFlagAlert show={appointment.red_flag_status} />
            <div className="rounded-md border border-teal-200 bg-teal-50 p-4 text-sm leading-6 text-teal-950">
              {appointment.doctor_summary || "No triage summary available."}
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="rounded-md bg-gray-50 p-4">
                <p className="text-sm text-gray-500">Main symptoms</p>
                <p className="mt-1 font-semibold text-gray-950">
                  {(appointment.structured_symptoms?.main_symptoms || []).join(", ") || "Not extracted"}
                </p>
              </div>
              <div className="rounded-md bg-gray-50 p-4">
                <p className="text-sm text-gray-500">Duration</p>
                <p className="mt-1 font-semibold text-gray-950">{appointment.structured_symptoms?.duration || "Not specified"}</p>
              </div>
              <div className="rounded-md bg-gray-50 p-4">
                <p className="text-sm text-gray-500">Severity</p>
                <p className="mt-1 font-semibold text-gray-950">
                  {appointment.structured_symptoms?.severity ? `${appointment.structured_symptoms.severity}/10` : "Not specified"}
                </p>
              </div>
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <p className="text-sm text-gray-600">
                <span className="font-semibold text-gray-800">Recommended specialty:</span>{" "}
                {appointment.recommended_specialty || "Not available"}
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-semibold text-gray-800">Red flag detected:</span>{" "}
                {appointment.red_flag_status ? "Yes" : "No"}
              </p>
              <p className="text-sm text-gray-600">
                <span className="font-semibold text-gray-800">AI confidence:</span>{" "}
                {appointment.ai_confidence ? `${Math.round(appointment.ai_confidence * 100)}%` : "Not available"}
              </p>
            </div>
            <details className="rounded-md border border-gray-200 p-4">
              <summary className="cursor-pointer text-sm font-semibold text-gray-800">Structured symptoms JSON</summary>
              <pre className="mt-3 overflow-x-auto rounded-md bg-gray-950 p-3 text-xs text-gray-100">
                {JSON.stringify(appointment.structured_symptoms || {}, null, 2)}
              </pre>
            </details>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
