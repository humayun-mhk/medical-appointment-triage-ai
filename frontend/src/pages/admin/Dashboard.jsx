import { useEffect, useState } from "react";

import api, { getApiError } from "../../api/axios.js";
import Card, { CardBody } from "../../components/Card.jsx";
import Loader from "../../components/Loader.jsx";

const labels = {
  total_patients: "Total Patients",
  total_doctors: "Total Doctors",
  total_appointments: "Total Appointments",
  todays_appointments: "Today's Appointments",
  completed_appointments: "Completed",
  cancelled_appointments: "Cancelled",
  available_slots: "Available Slots",
};

export default function AdminDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/admin/dashboard")
      .then(({ data }) => setStats(data))
      .catch((err) => setError(getApiError(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader label="Loading admin dashboard" />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-950">Admin Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">Operational overview for the appointment platform.</p>
      </div>
      {error && <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats &&
          Object.entries(labels).map(([key, label]) => (
            <Card key={key}>
              <CardBody>
                <p className="text-sm font-medium text-gray-500">{label}</p>
                <p className="mt-2 text-3xl font-bold text-gray-950">{stats[key] ?? 0}</p>
              </CardBody>
            </Card>
          ))}
      </div>
    </div>
  );
}
