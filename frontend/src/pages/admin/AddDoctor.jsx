import { zodResolver } from "@hookform/resolvers/zod";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import api, { getApiError } from "../../api/axios.js";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import Input from "../../components/Input.jsx";
import Loader from "../../components/Loader.jsx";
import Select from "../../components/Select.jsx";
import { doctorSchema } from "../../schemas/admin.js";

export default function AddDoctor() {
  const [specialties, setSpecialties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(doctorSchema),
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
      specialty_id: "",
      qualification: "",
      experience_years: 0,
      bio: "",
      consultation_fee: 0,
      clinic_address: "",
    },
  });

  useEffect(() => {
    api
      .get("/admin/specialties")
      .then(({ data }) => setSpecialties(data))
      .catch((err) => setError(getApiError(err)))
      .finally(() => setLoading(false));
  }, []);

  async function onSubmit(values) {
    setMessage("");
    setError("");
    try {
      await api.post("/admin/doctors", {
        ...values,
        specialty_id: Number(values.specialty_id),
        experience_years: Number(values.experience_years),
        consultation_fee: Number(values.consultation_fee),
      });
      reset();
      setMessage("Doctor account created successfully.");
    } catch (err) {
      setError(getApiError(err, "Unable to create doctor"));
    }
  }

  if (loading) return <Loader label="Loading specialties" />;

  return (
    <Card>
      <CardHeader title="Add Doctor" description="Create a doctor user and profile." />
      <CardBody>
        {message && <div className="mb-4 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</div>}
        {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
          <div className="form-grid">
            <Input label="Full name" error={errors.full_name?.message} {...register("full_name")} />
            <Input label="Email" type="email" error={errors.email?.message} {...register("email")} />
            <Input label="Password" type="password" error={errors.password?.message} {...register("password")} />
            <Select label="Specialty" error={errors.specialty_id?.message} {...register("specialty_id")}>
              <option value="">Select specialty</option>
              {specialties.map((specialty) => (
                <option key={specialty.id} value={specialty.id}>
                  {specialty.name}
                </option>
              ))}
            </Select>
            <Input label="Qualification" error={errors.qualification?.message} {...register("qualification")} />
            <Input label="Experience years" type="number" min="0" error={errors.experience_years?.message} {...register("experience_years")} />
            <Input label="Consultation fee" type="number" min="0" step="0.01" error={errors.consultation_fee?.message} {...register("consultation_fee")} />
          </div>
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">Clinic address</span>
            <textarea className="min-h-24 w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100" {...register("clinic_address")} />
            {errors.clinic_address && <span className="mt-1 block text-sm text-rose-600">{errors.clinic_address.message}</span>}
          </label>
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">Bio</span>
            <textarea className="min-h-28 w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100" {...register("bio")} />
          </label>
          <Button type="submit" isLoading={isSubmitting}>
            Create Doctor
          </Button>
        </form>
      </CardBody>
    </Card>
  );
}
