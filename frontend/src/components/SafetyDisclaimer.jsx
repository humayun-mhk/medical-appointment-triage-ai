export default function SafetyDisclaimer({ compact = false }) {
  return (
    <div className={`rounded-md border border-teal-200 bg-teal-50 text-teal-900 ${compact ? "px-3 py-2 text-xs" : "p-4 text-sm"}`}>
      This tool does not provide diagnosis, prescribe medicine, or replace a doctor. It only helps route you to a suitable healthcare professional.
    </div>
  );
}
