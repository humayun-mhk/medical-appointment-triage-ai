import { Link, NavLink } from "react-router-dom";

import { useAuth } from "../hooks/useAuth.js";
import { getRoleHome } from "../utils/roles.js";
import Button from "./Button.jsx";

export default function Navbar({ links = [] }) {
  const { user, logout } = useAuth();

  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <Link to={user ? getRoleHome(user.role) : "/"} className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-md bg-teal-600 text-sm font-bold text-white">
            HC
          </span>
          <span className="font-semibold text-gray-950">HealthCare Appointments</span>
        </Link>
        <nav className="flex flex-wrap items-center gap-2">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `rounded-md px-3 py-2 text-sm font-medium ${
                  isActive ? "bg-teal-50 text-teal-700" : "text-gray-600 hover:bg-gray-50"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
          {user ? (
            <Button variant="secondary" onClick={logout} className="min-h-9">
              Sign out
            </Button>
          ) : (
            <>
              <Link className="rounded-md px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50" to="/login">
                Login
              </Link>
              <Link className="rounded-md bg-teal-600 px-3 py-2 text-sm font-semibold text-white hover:bg-teal-700" to="/register">
                Register
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
