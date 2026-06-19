export default function EmptyState({ title = "Nothing here yet", message, action }) {
  return (
    <div className="rounded-lg border border-dashed border-gray-300 bg-white px-6 py-10 text-center">
      <h3 className="text-base font-semibold text-gray-950">{title}</h3>
      {message && <p className="mx-auto mt-2 max-w-md text-sm text-gray-500">{message}</p>}
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
