import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import api, { getApiError } from "../../api/axios.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Input from "../../components/Input.jsx";
import Loader from "../../components/Loader.jsx";
import Table from "../../components/Table.jsx";
import { availabilitySchema } from "../../schemas/doctor.js";
import { formatDateTime } from "../../utils/format.js";

export default function DoctorAvailability() {
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(availabilitySchema),
    defaultValues: { start_time: "", end_time: "" },
  });

  async function loadSlots() {
    try {
      const { data } = await api.get("/doctor/availability");
      setSlots(data);
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSlots();
  }, []);

  async function onSubmit(values) {
    setError("");
    setMessage("");
    try {
      await api.post("/doctor/availability", {
        start_time: new Date(values.start_time).toISOString(),
        end_time: new Date(values.end_time).toISOString(),
      });
      reset();
      setMessage("Slot created successfully.");
      await loadSlots();
    } catch (err) {
      setError(getApiError(err, "Unable to create slot"));
    }
  }

  if (loading) return <Loader label="Loading availability" />;

  return (
    <div className="grid gap-6 lg:grid-cols-[0.8fr_1.2fr]">
      <Card>
        <CardHeader title="Create Availability" />
        <CardBody>
          {message && <div className="mb-4 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</div>}
          {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <Input label="Start time" type="datetime-local" error={errors.start_time?.message} {...register("start_time")} />
            <Input label="End time" type="datetime-local" error={errors.end_time?.message} {...register("end_time")} />
            <Button type="submit" isLoading={isSubmitting}>
              Create Slot
            </Button>
          </form>
        </CardBody>
      </Card>

      <Card>
        <CardHeader title="My Slots" />
        <CardBody>
          {slots.length === 0 ? (
            <EmptyState title="No slots created" />
          ) : (
            <Table
              columns={["Start", "End", "Status"]}
              rows={slots}
              renderRow={(slot) => (
                <tr key={slot.id}>
                  <td className="px-4 py-3 text-gray-600">{formatDateTime(slot.start_time)}</td>
                  <td className="px-4 py-3 text-gray-600">{formatDateTime(slot.end_time)}</td>
                  <td className="px-4 py-3"><Badge>{slot.status}</Badge></td>
                </tr>
              )}
            />
          )}
        </CardBody>
      </Card>
    </div>
  );
}
