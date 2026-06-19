import { Outlet } from "react-router-dom";

import Navbar from "../components/Navbar.jsx";

const links = [
  { to: "/admin/dashboard", label: "Dashboard" },
  { to: "/admin/analytics", label: "Analytics" },
  { to: "/admin/specialties/new", label: "Add Specialty" },
  { to: "/admin/doctors/new", label: "Add Doctor" },
  { to: "/admin/slots/new", label: "Create Slots" },
  { to: "/admin/doctors", label: "Doctors" },
  { to: "/admin/patients", label: "Patients" },
  { to: "/admin/appointments", label: "Appointments" },
  { to: "/admin/triage-sessions", label: "Triage" },
  { to: "/admin/review-cases", label: "Review" },
  { to: "/admin/knowledge-base", label: "Knowledge" },
  { to: "/admin/notification-logs", label: "Notifications" },
  { to: "/admin/ai-audit-logs", label: "AI Audit" },
  { to: "/admin/security-audit-logs", label: "Security" },
];

export default function AdminLayout() {
  return (
    <>
      <Navbar links={links} />
      <main className="page-shell">
        <Outlet />
      </main>
    </>
  );
}
