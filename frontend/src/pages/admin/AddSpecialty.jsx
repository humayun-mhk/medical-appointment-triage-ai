import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";

import api, { getApiError } from "../../api/axios.js";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import Input from "../../components/Input.jsx";
import { specialtySchema } from "../../schemas/admin.js";

export default function AddSpecialty() {
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(specialtySchema),
    defaultValues: { name: "", description: "" },
  });

  async function onSubmit(values) {
    setMessage("");
    setError("");
    try {
      await api.post("/admin/specialties", values);
      reset();
      setMessage("Specialty created successfully.");
    } catch (err) {
      setError(getApiError(err, "Unable to create specialty"));
    }
  }

  return (
    <Card className="max-w-2xl">
      <CardHeader title="Add Specialty" />
      <CardBody>
        {message && <div className="mb-4 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</div>}
        {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
          <Input label="Name" error={errors.name?.message} {...register("name")} />
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">Description</span>
            <textarea className="min-h-28 w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100" {...register("description")} />
          </label>
          <Button type="submit" isLoading={isSubmitting}>
            Create Specialty
          </Button>
        </form>
      </CardBody>
    </Card>
  );
}
