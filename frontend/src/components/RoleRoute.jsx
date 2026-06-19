import { Navigate, Outlet } from "react-router-dom";

import { useAuth } from "../hooks/useAuth.js";
import { getRoleHome } from "../utils/roles.js";

export default function RoleRoute({ roles }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (!roles.includes(user.role)) return <Navigate to={getRoleHome(user.role)} replace />;
  return <Outlet />;
}
