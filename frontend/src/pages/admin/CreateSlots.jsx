import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import api, { getApiError } from "../../api/axios.js";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import Input from "../../components/Input.jsx";
import Loader from "../../components/Loader.jsx";
import Select from "../../components/Select.jsx";
import { adminSlotSchema } from "../../schemas/admin.js";

export default function CreateSlots() {
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(adminSlotSchema),
    defaultValues: { doctor_id: "", start_time: "", end_time: "" },
  });

  useEffect(() => {
    api
      .get("/admin/doctors")
      .then(({ data }) => setDoctors(data))
      .catch((err) => setError(getApiError(err)))
      .finally(() => setLoading(false));
  }, []);

  async function onSubmit(values) {
    setMessage("");
    setError("");
    try {
      await api.post("/admin/slots", {
        doctor_id: Number(values.doctor_id),
        start_time: new Date(values.start_time).toISOString(),
        end_time: new Date(values.end_time).toISOString(),
      });
      reset();
      setMessage("Doctor slot created successfully.");
    } catch (err) {
      setError(getApiError(err, "Unable to create slot"));
    }
  }

  if (loading) return <Loader label="Loading doctors" />;

  return (
    <Card className="max-w-2xl">
      <CardHeader title="Create Doctor Slot" />
      <CardBody>
        {message && <div className="mb-4 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</div>}
        {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          <Select label="Doctor" error={errors.doctor_id?.message} {...register("doctor_id")}>
            <option value="">Select doctor</option>
            {doctors.map((doctor) => (
              <option key={doctor.id} value={doctor.id}>
                {doctor.full_name} - {doctor.specialty?.name}
              </option>
            ))}
          </Select>
          <Input label="Start time" type="datetime-local" error={errors.start_time?.message} {...register("start_time")} />
          <Input label="End time" type="datetime-local" error={errors.end_time?.message} {...register("end_time")} />
          <Button type="submit" isLoading={isSubmitting}>
            Create Slot
          </Button>
        </form>
      </CardBody>
    </Card>
  );
}
