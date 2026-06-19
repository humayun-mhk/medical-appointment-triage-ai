import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { getApiError } from "../../api/axios.js";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import Input from "../../components/Input.jsx";
import Navbar from "../../components/Navbar.jsx";
import { useAuth } from "../../hooks/useAuth.js";
import { registerSchema } from "../../schemas/auth.js";
import { getRoleHome } from "../../utils/roles.js";

export default function Register() {
  const { user, register: registerPatient } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(registerSchema),
    defaultValues: { full_name: "", email: "", password: "", confirmPassword: "" },
  });

  if (user) return <Navigate to={getRoleHome(user.role)} replace />;

  async function onSubmit(values) {
    setError("");
    try {
      const nextUser = await registerPatient({
        full_name: values.full_name,
        email: values.email,
        password: values.password,
      });
      navigate(getRoleHome(nextUser.role), { replace: true });
    } catch (err) {
      setError(getApiError(err, "Unable to register"));
    }
  }

  return (
    <>
      <Navbar />
      <main className="page-shell flex min-h-[calc(100vh-110px)] items-center justify-center">
        <Card className="w-full max-w-lg">
          <CardHeader title="Patient Registration" description="Create your patient account." />
          <CardBody>
            {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
            <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
              <Input label="Full name" error={errors.full_name?.message} {...register("full_name")} />
              <Input label="Email" type="email" error={errors.email?.message} {...register("email")} />
              <div className="grid gap-4 sm:grid-cols-2">
                <Input label="Password" type="password" error={errors.password?.message} {...register("password")} />
                <Input
                  label="Confirm password"
                  type="password"
                  error={errors.confirmPassword?.message}
                  {...register("confirmPassword")}
                />
              </div>
              <Button type="submit" className="w-full" isLoading={isSubmitting}>
                Create Account
              </Button>
            </form>
            <p className="mt-5 text-center text-sm text-gray-600">
              Already registered?{" "}
              <Link className="font-semibold text-teal-700" to="/login">
                Login
              </Link>
            </p>
          </CardBody>
        </Card>
      </main>
    </>
  );
}
