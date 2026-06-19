import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import api, { getApiError } from "../../api/axios.js";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import Input from "../../components/Input.jsx";
import Loader from "../../components/Loader.jsx";
import Select from "../../components/Select.jsx";
import { patientProfileSchema } from "../../schemas/patient.js";

function cleanPayload(values) {
  return Object.fromEntries(
    Object.entries(values).map(([key, value]) => [key, value === "" ? null : value])
  );
}

export default function PatientProfile() {
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(patientProfileSchema),
    defaultValues: {
      date_of_birth: "",
      gender: "",
      phone: "",
      address: "",
      blood_group: "",
      allergies: "",
      chronic_conditions: "",
      emergency_contact: "",
    },
  });

  useEffect(() => {
    async function loadProfile() {
      try {
        const { data } = await api.get("/patients/profile");
        reset({
          date_of_birth: data.date_of_birth || "",
          gender: data.gender || "",
          phone: data.phone || "",
          address: data.address || "",
          blood_group: data.blood_group || "",
          allergies: data.allergies || "",
          chronic_conditions: data.chronic_conditions || "",
          emergency_contact: data.emergency_contact || "",
        });
      } catch (err) {
        if (err.response?.status !== 404) setError(getApiError(err));
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, [reset]);

  async function onSubmit(values) {
    setMessage("");
    setError("");
    try {
      await api.post("/patients/profile", cleanPayload(values));
      setMessage("Profile saved successfully.");
    } catch (err) {
      setError(getApiError(err, "Unable to save profile"));
    }
  }

  if (loading) return <Loader label="Loading profile" />;

  return (
    <Card>
      <CardHeader title="Patient Profile" description="Keep your health and contact details current." />
      <CardBody>
        {message && <div className="mb-4 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</div>}
        {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
          <div className="form-grid">
            <Input label="Date of birth" type="date" error={errors.date_of_birth?.message} {...register("date_of_birth")} />
            <Select label="Gender" error={errors.gender?.message} {...register("gender")}>
              <option value="">Select gender</option>
              <option value="Female">Female</option>
              <option value="Male">Male</option>
              <option value="Other">Other</option>
            </Select>
            <Input label="Phone" error={errors.phone?.message} {...register("phone")} />
            <Input label="Blood group" error={errors.blood_group?.message} {...register("blood_group")} />
            <Input label="Emergency contact" error={errors.emergency_contact?.message} {...register("emergency_contact")} />
          </div>
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">Address</span>
            <textarea className="min-h-24 w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100" {...register("address")} />
          </label>
          <div className="form-grid">
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-gray-700">Allergies</span>
              <textarea className="min-h-24 w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100" {...register("allergies")} />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm font-medium text-gray-700">Chronic conditions</span>
              <textarea className="min-h-24 w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100" {...register("chronic_conditions")} />
            </label>
          </div>
          <Button type="submit" isLoading={isSubmitting}>
            Save Profile
          </Button>
        </form>
      </CardBody>
    </Card>
  );
}
