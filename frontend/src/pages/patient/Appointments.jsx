import { useEffect, useState } from "react";

import api, { getApiError } from "../../api/axios.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import Table from "../../components/Table.jsx";
import UrgencyBadge from "../../components/UrgencyBadge.jsx";
import { formatDateTime } from "../../utils/format.js";

export default function PatientAppointments() {
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busyId, setBusyId] = useState(null);

  async function load() {
    try {
      const { data } = await api.get("/appointments/my");
      setAppointments(data);
    } catch (err) {
      if (err.response?.status !== 404) setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function cancelAppointment(appointmentId) {
    setBusyId(appointmentId);
    setError("");
    try {
      await api.post(`/appointments/${appointmentId}/cancel`);
      await load();
    } catch (err) {
      setError(getApiError(err, "Unable to cancel appointment"));
    } finally {
      setBusyId(null);
    }
  }

  if (loading) return <Loader label="Loading appointments" />;

  return (
    <Card>
      <CardHeader title="My Appointments" description="View appointment history and cancel booked visits." />
      <CardBody>
        {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        {appointments.length === 0 ? (
          <EmptyState title="No appointments yet" message="Your booked visits will appear here." />
        ) : (
          <Table
            columns={["Patient", "Doctor", "Specialty", "Date and Time", "Symptoms", "Urgency", "Status", "Action"]}
            rows={appointments}
            renderRow={(appointment) => (
              <tr key={appointment.id}>
                <td className="px-4 py-3 font-medium text-gray-950">{appointment.patient_name || "You"}</td>
                <td className="px-4 py-3 font-medium text-gray-950">{appointment.doctor?.full_name}</td>
                <td className="px-4 py-3 text-gray-600">{appointment.doctor?.specialty?.name}</td>
                <td className="px-4 py-3 text-gray-600">{formatDateTime(appointment.slot?.start_time)}</td>
                <td className="max-w-xs px-4 py-3 text-gray-600">{appointment.symptoms || "None"}</td>
                <td className="px-4 py-3">{appointment.urgency_level ? <UrgencyBadge level={appointment.urgency_level} /> : "N/A"}</td>
                <td className="px-4 py-3"><Badge>{appointment.status}</Badge></td>
                <td className="px-4 py-3">
                  {appointment.status === "booked" ? (
                    <Button
                      variant="danger"
                      isLoading={busyId === appointment.id}
                      onClick={() => cancelAppointment(appointment.id)}
                    >
                      Cancel
                    </Button>
                  ) : (
                    <span className="text-sm text-gray-400">No action</span>
                  )}
                </td>
              </tr>
            )}
          />
        )}
      </CardBody>
    </Card>
  );
}
