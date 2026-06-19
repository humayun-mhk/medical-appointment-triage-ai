import { Link, Navigate } from "react-router-dom";

import Button from "../components/Button.jsx";
import Card, { CardBody } from "../components/Card.jsx";
import Navbar from "../components/Navbar.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { getRoleHome } from "../utils/roles.js";

export default function Home() {
  const { user } = useAuth();
  if (user) return <Navigate to={getRoleHome(user.role)} replace />;

  return (
    <>
      <Navbar />
      <main className="page-shell">
        <div className="grid min-h-[calc(100vh-130px)] items-center gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <section>
            <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
              Healthcare Appointment System
            </p>
            <h1 className="mt-3 max-w-3xl text-4xl font-bold text-gray-950 sm:text-5xl">
              Book visits, manage availability, and keep clinics coordinated.
            </h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-gray-600">
              A role-based platform for patients, doctors, and administrators to handle appointments without AI features in Step 1.
            </p>
            <div className="mt-7 flex flex-wrap gap-3">
              <Link to="/register">
                <Button>Register as Patient</Button>
              </Link>
              <Link to="/login">
                <Button variant="secondary">Login</Button>
              </Link>
            </div>
          </section>

          <Card>
            <CardBody className="space-y-4">
              {[
                ["Patients", "Create a profile, find doctors, book slots, and cancel booked visits."],
                ["Doctors", "Review schedules, add notes, update statuses, and create availability."],
                ["Admins", "Manage specialties, doctors, slots, patients, appointments, and dashboard stats."],
              ].map(([title, text]) => (
                <div key={title} className="rounded-md border border-gray-200 bg-gray-50 p-4">
                  <h2 className="font-semibold text-gray-950">{title}</h2>
                  <p className="mt-1 text-sm leading-6 text-gray-600">{text}</p>
                </div>
              ))}
            </CardBody>
          </Card>
        </div>
      </main>
    </>
  );
}
