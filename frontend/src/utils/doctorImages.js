export function generatedDoctorImageUrl(doctorOrName) {
  const rawName =
    typeof doctorOrName === "string"
      ? doctorOrName
      : doctorOrName?.full_name || doctorOrName?.doctor_name || `doctor-${doctorOrName?.id || doctorOrName?.doctor_id || "profile"}`;
  const seed = encodeURIComponent(String(rawName).toLowerCase());
  return `https://api.dicebear.com/10.x/personas/svg?seed=${seed}&backgroundColor=d1fae5,dbeafe,fef3c7,fee2e2&radius=12`;
}
