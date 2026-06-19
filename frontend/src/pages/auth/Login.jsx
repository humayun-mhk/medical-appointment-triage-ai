import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { getApiError } from "../../api/axios.js";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import Input from "../../components/Input.jsx";
import Navbar from "../../components/Navbar.jsx";
import { useAuth } from "../../hooks/useAuth.js";
import { loginSchema } from "../../schemas/auth.js";
import { getRoleHome } from "../../utils/roles.js";

export default function Login() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  if (user) return <Navigate to={getRoleHome(user.role)} replace />;

  async function onSubmit(values) {
    setError("");
    try {
      const nextUser = await login(values);
      navigate(location.state?.from?.pathname || getRoleHome(nextUser.role), { replace: true });
    } catch (err) {
      setError(getApiError(err, "Unable to login"));
    }
  }

  return (
    <>
      <Navbar />
      <main className="page-shell flex min-h-[calc(100vh-110px)] items-center justify-center">
        <Card className="w-full max-w-md">
          <CardHeader title="Login" description="Access your role-based workspace." />
          <CardBody>
            {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
            <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
              <Input label="Email" type="email" error={errors.email?.message} {...register("email")} />
              <Input label="Password" type="password" error={errors.password?.message} {...register("password")} />
              <Button type="submit" className="w-full" isLoading={isSubmitting}>
                Login
              </Button>
            </form>
            <p className="mt-5 text-center text-sm text-gray-600">
              Need an account?{" "}
              <Link className="font-semibold text-teal-700" to="/register">
                Register
              </Link>
            </p>
          </CardBody>
        </Card>
      </main>
    </>
  );
}
