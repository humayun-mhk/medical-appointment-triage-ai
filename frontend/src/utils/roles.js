export const roleHome = {
  patient: "/patient/dashboard",
  doctor: "/doctor/dashboard",
  admin: "/admin/dashboard",
};

export function getRoleHome(role) {
  return roleHome[role] || "/";
}
