import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import api, { getApiError } from "../../api/axios.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import Table from "../../components/Table.jsx";
import UrgencyBadge from "../../components/UrgencyBadge.jsx";
import { formatDateTime } from "../../utils/format.js";

export default function TodayAppointments() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/doctor/appointments", { params: { filter: "today" } })
      .then(({ data }) => setAppointments(data))
      .catch((err) => setError(getApiError(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader label="Loading today's appointments" />;

  return (
    <Card>
      <CardHeader title="Today's Appointments" />
      <CardBody>
        {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        {appointments.length === 0 ? (
          <EmptyState title="No appointments today" />
        ) : (
          <Table
            columns={["Patient", "Time", "Symptoms", "Urgency", "Status", "Action"]}
            rows={appointments}
            renderRow={(appointment) => (
              <tr key={appointment.appointment_id}>
                <td className="px-4 py-3 font-medium text-gray-950">{appointment.patient?.full_name}</td>
                <td className="px-4 py-3 text-gray-600">{formatDateTime(appointment.slot_start_time)}</td>
                <td className="max-w-sm px-4 py-3 text-gray-600">{appointment.symptoms || "None"}</td>
                <td className="px-4 py-3">{appointment.urgency_level ? <UrgencyBadge level={appointment.urgency_level} /> : "N/A"}</td>
                <td className="px-4 py-3"><Badge>{appointment.status}</Badge></td>
                <td className="px-4 py-3">
                  <Link to={`/doctor/appointments/${appointment.appointment_id}`}>
                    <Button variant="secondary">View Details</Button>
                  </Link>
                </td>
              </tr>
            )}
          />
        )}
      </CardBody>
    </Card>
  );
}
