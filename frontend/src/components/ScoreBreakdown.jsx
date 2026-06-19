export default function ScoreBreakdown({ breakdown = {} }) {
  return (
    <div className="grid gap-2 text-xs text-gray-600 sm:grid-cols-2">
      {Object.entries(breakdown).map(([key, value]) => (
        <div key={key} className="flex justify-between rounded-md bg-gray-50 px-3 py-2">
          <span>{key.replace("_", " ")}</span>
          <span className="font-semibold text-gray-900">{value}</span>
        </div>
      ))}
    </div>
  );
}
