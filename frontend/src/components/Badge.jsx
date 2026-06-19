const statusStyles = {
  booked: "bg-sky-100 text-sky-700 ring-sky-200",
  completed: "bg-emerald-100 text-emerald-700 ring-emerald-200",
  cancelled: "bg-rose-100 text-rose-700 ring-rose-200",
  no_show: "bg-amber-100 text-amber-800 ring-amber-200",
  available: "bg-emerald-100 text-emerald-700 ring-emerald-200",
  active: "bg-emerald-100 text-emerald-700 ring-emerald-200",
  pending: "bg-amber-100 text-amber-800 ring-amber-200",
  in_review: "bg-sky-100 text-sky-700 ring-sky-200",
  resolved: "bg-emerald-100 text-emerald-700 ring-emerald-200",
  dismissed: "bg-gray-100 text-gray-700 ring-gray-200",
  low: "bg-gray-100 text-gray-700 ring-gray-200",
  medium: "bg-amber-100 text-amber-800 ring-amber-200",
  high: "bg-orange-100 text-orange-800 ring-orange-200",
  critical: "bg-rose-100 text-rose-700 ring-rose-200",
  urgent: "bg-orange-100 text-orange-800 ring-orange-200",
  emergency: "bg-rose-100 text-rose-700 ring-rose-200",
  sent: "bg-emerald-100 text-emerald-700 ring-emerald-200",
  failed: "bg-rose-100 text-rose-700 ring-rose-200",
  email: "bg-sky-100 text-sky-700 ring-sky-200",
  sms: "bg-teal-100 text-teal-700 ring-teal-200",
  whatsapp: "bg-emerald-100 text-emerald-700 ring-emerald-200",
  in_app: "bg-violet-100 text-violet-700 ring-violet-200",
  specialty_description: "bg-teal-100 text-teal-700 ring-teal-200",
  clinic_policy: "bg-sky-100 text-sky-700 ring-sky-200",
  emergency_policy: "bg-rose-100 text-rose-700 ring-rose-200",
  doctor_service: "bg-indigo-100 text-indigo-700 ring-indigo-200",
  faq: "bg-gray-100 text-gray-700 ring-gray-200",
  cancellation_policy: "bg-amber-100 text-amber-800 ring-amber-200",
  patient_preparation: "bg-emerald-100 text-emerald-700 ring-emerald-200",
  safety_guideline: "bg-orange-100 text-orange-800 ring-orange-200",
};

export default function Badge({ children, tone }) {
  const key = tone || String(children).toLowerCase();
  return (
    <span
      className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${
        statusStyles[key] || "bg-gray-100 text-gray-700 ring-gray-200"
      }`}
    >
      {String(children).replace("_", " ")}
    </span>
  );
}
