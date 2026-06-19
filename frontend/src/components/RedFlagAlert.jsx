export default function RedFlagAlert({ show, message }) {
  if (!show) return null;
  return (
    <div className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-rose-800">
      <h3 className="font-semibold">Emergency Warning</h3>
      <p className="mt-1 text-sm leading-6">
        {message ||
          "Your symptoms may require emergency care. Please contact local emergency services or visit the nearest emergency department."}
      </p>
    </div>
  );
}
