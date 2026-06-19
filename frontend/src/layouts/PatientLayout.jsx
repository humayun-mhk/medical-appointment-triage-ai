import { Outlet } from "react-router-dom";

import Navbar from "../components/Navbar.jsx";

const links = [
  { to: "/patient/dashboard", label: "Dashboard" },
  { to: "/patient/profile", label: "Profile" },
  { to: "/patient/triage", label: "Triage" },
  { to: "/patient/specialties", label: "Specialties" },
  { to: "/patient/doctors", label: "Doctors" },
  { to: "/patient/appointments", label: "Appointments" },
];

export default function PatientLayout() {
  return (
    <>
      <Navbar links={links} />
      <main className="page-shell">
        <Outlet />
      </main>
    </>
  );
}
