import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import api, { getApiError } from "../../api/axios.js";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import Select from "../../components/Select.jsx";
import { appointmentBookSchema } from "../../schemas/patient.js";
import { formatDateTime } from "../../utils/format.js";

export default function PatientBookAppointment() {
  const { doctorId } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [doctor, setDoctor] = useState(null);
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(appointmentBookSchema),
    defaultValues: { slot_id: searchParams.get("slot_id") || "", symptoms: "", patient_notes: "" },
  });

  useEffect(() => {
    async function load() {
      try {
        const [doctorResponse, slotResponse] = await Promise.all([
          api.get(`/doctors/${doctorId}`),
          api.get(`/doctors/${doctorId}/slots`),
        ]);
        setDoctor(doctorResponse.data);
        setSlots(slotResponse.data);
        reset({ slot_id: searchParams.get("slot_id") || "", symptoms: "", patient_notes: "" });
      } catch (err) {
        setError(getApiError(err));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [doctorId, reset, searchParams]);

  async function onSubmit(values) {
    setError("");
    try {
      await api.post("/appointments/book", {
        doctor_id: Number(doctorId),
        slot_id: Number(values.slot_id),
        symptoms: values.symptoms || null,
        patient_notes: values.patient_notes || null,
      });
      navigate("/patient/appointments", { replace: true });
    } catch (err) {
      setError(getApiError(err, "Unable to book appointment"));
    }
  }

  if (loading) return <Loader label="Loading booking form" />;
  if (!doctor) return <EmptyState title="Doctor not found" message={error} />;

  return (
    <Card>
      <CardHeader title={`Book ${doctor.full_name}`} description={doctor.specialty?.name} />
      <CardBody>
        {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        {slots.length === 0 ? (
          <EmptyState title="No available slots" message="This doctor has no open slots right now." />
        ) : (
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <Select label="Available slot" error={errors.slot_id?.message} {...register("slot_id")}>
              <option value="">Select a slot</option>
              {slots.map((slot) => (
                <option key={slot.id} value={slot.id}>
                  {formatDateTime(slot.start_time)}
                </option>
              ))}
            </Select>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-gray-700">Symptoms</span>
              <textarea className="min-h-28 w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100" {...register("symptoms")} />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-gray-700">Patient notes</span>
              <textarea className="min-h-28 w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100" {...register("patient_notes")} />
            </label>
            <Button type="submit" isLoading={isSubmitting}>
              Confirm Booking
            </Button>
          </form>
        )}
      </CardBody>
    </Card>
  );
}
