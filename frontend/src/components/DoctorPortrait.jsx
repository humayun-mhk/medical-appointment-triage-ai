import { generatedDoctorImageUrl } from "../utils/doctorImages.js";

export default function DoctorPortrait({ doctor, name, className = "" }) {
  const label = name || doctor?.full_name || doctor?.doctor_name || "Doctor";
  const src = doctor?.image_url || generatedDoctorImageUrl(doctor || label);

  return (
    <img
      src={src}
      alt={`${label} profile`}
      loading="lazy"
      className={`shrink-0 rounded-md border border-gray-200 bg-gray-50 object-cover ${className}`}
    />
  );
}
