const styles = {
  routine: "bg-gray-100 text-gray-700 ring-gray-200",
  soon: "bg-sky-100 text-sky-700 ring-sky-200",
  urgent: "bg-orange-100 text-orange-800 ring-orange-200",
  emergency: "bg-rose-100 text-rose-700 ring-rose-200",
};

export default function UrgencyBadge({ level }) {
  const value = level || "routine";
  return (
    <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${styles[value] || styles.routine}`}>
      {value}
    </span>
  );
}
