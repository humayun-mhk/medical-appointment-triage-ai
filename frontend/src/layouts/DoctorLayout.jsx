import { Outlet } from "react-router-dom";

import Navbar from "../components/Navbar.jsx";

const links = [
  { to: "/doctor/dashboard", label: "Dashboard" },
  { to: "/doctor/today", label: "Today" },
  { to: "/doctor/availability", label: "Availability" },
];

export default function DoctorLayout() {
  return (
    <>
      <Navbar links={links} />
      <main className="page-shell">
        <Outlet />
      </main>
    </>
  );
}
