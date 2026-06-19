import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import api, { getApiError } from "../../api/axios.js";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import Badge from "../../components/Badge.jsx";
import UrgencyBadge from "../../components/UrgencyBadge.jsx";
import { formatDateTime } from "../../utils/format.js";

export default function DoctorDashboard() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/doctor/appointments")
      .then(({ data }) => setAppointments(data))
      .catch((err) => setError(getApiError(err)))
      .finally(() => setLoading(false));
  }, []);

  const stats = useMemo(() => {
    const today = new Date().toDateString();
    return [
      ["Today", appointments.filter((item) => new Date(item.slot_start_time).toDateString() === today).length],
      ["Upcoming", appointments.filter((item) => item.status === "booked" && new Date(item.slot_start_time) >= new Date()).length],
      ["Completed", appointments.filter((item) => item.status === "completed").length],
      ["Cancelled", appointments.filter((item) => item.status === "cancelled").length],
    ];
  }, [appointments]);

  if (loading) return <Loader label="Loading doctor dashboard" />;

  return (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-950">Doctor Dashboard</h1>
          <p className="mt-1 text-sm text-gray-500">Monitor appointments and availability.</p>
        </div>
        <Link to="/doctor/availability">
          <Button>Manage Availability</Button>
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
        <CardHeader title="Next Appointments" />
        <CardBody>
          {appointments.length === 0 ? (
            <EmptyState title="No appointments assigned" />
          ) : (
            <div className="space-y-3">
              {appointments.slice(0, 6).map((appointment) => (
                <div key={appointment.appointment_id} className="flex flex-col gap-3 rounded-md border border-gray-200 p-4 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <p className="font-semibold text-gray-950">{appointment.patient?.full_name}</p>
                    <p className="text-sm text-gray-500">{formatDateTime(appointment.slot_start_time)}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    {appointment.urgency_level && <UrgencyBadge level={appointment.urgency_level} />}
                    <Badge>{appointment.status}</Badge>
                    <Link to={`/doctor/appointments/${appointment.appointment_id}`}>
                      <Button variant="secondary">View Details</Button>
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
