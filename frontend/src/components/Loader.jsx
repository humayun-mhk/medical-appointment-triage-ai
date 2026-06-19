export default function Loader({ label = "Loading" }) {
  return (
    <div className="flex min-h-32 items-center justify-center rounded-lg border border-dashed border-gray-200 bg-white text-sm font-medium text-gray-500">
      {label}
    </div>
  );
}
