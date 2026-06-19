import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import api, { getApiError } from "../../api/axios.js";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import Badge from "../../components/Badge.jsx";
import { formatDateTime } from "../../utils/format.js";

export default function PatientDashboard() {
  const [dashboard, setDashboard] = useState({
    stats: { upcoming: 0, total: 0, cancelled: 0, completed: 0 },
    upcoming_appointments: [],
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const { data } = await api.get("/patients/dashboard");
        setDashboard(data);
      } catch (err) {
        if (err.response?.status !== 404) setError(getApiError(err));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const stats = [
    ["Upcoming", dashboard.stats.upcoming],
    ["Total", dashboard.stats.total],
    ["Cancelled", dashboard.stats.cancelled],
    ["Completed", dashboard.stats.completed],
  ];
  const upcomingAppointments = dashboard.upcoming_appointments || [];

  if (loading) return <Loader label="Loading patient dashboard" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-950">Patient Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">Your appointments and booking activity.</p>
        </div>
        <Link to="/patient/doctors">
          <Button>Find Doctors</Button>
        </Link>
      </div>

      {error && <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map(([label, value]) => (
          <Card key={label}>
            <CardBody>
              <p className="text-sm font-medium text-gray-500">{label}</p>
              <p className="mt-2 text-3xl font-bold text-gray-950">{value}</p>
            </CardBody>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader title="Upcoming Appointments" />
        <CardBody>
          {upcomingAppointments.length === 0 ? (
            <EmptyState
              title="No upcoming appointments"
              message="Browse available doctors and book a slot when you are ready."
              action={
                <Link to="/patient/doctors">
                  <Button>Browse Doctors</Button>
                </Link>
              }
            />
          ) : (
            <div className="space-y-3">
              {upcomingAppointments.map((appointment) => (
                <div key={appointment.id} className="flex flex-col gap-3 rounded-md border border-gray-200 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-semibold text-gray-950">{appointment.doctor?.full_name}</p>
                    <p className="text-sm text-gray-500">{formatDateTime(appointment.slot?.start_time)}</p>
                  </div>
                  <Badge>{appointment.status}</Badge>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
