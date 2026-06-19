import { useEffect, useState } from "react";

import api, { getApiError } from "../../api/axios.js";
import Badge from "../../components/Badge.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import Select from "../../components/Select.jsx";
import Table from "../../components/Table.jsx";
import UrgencyBadge from "../../components/UrgencyBadge.jsx";
import { formatDateTime } from "../../utils/format.js";

export default function ManageAppointments() {
  const [appointments, setAppointments] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [filters, setFilters] = useState({ status: "", doctor_id: "", date: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/admin/doctors")
      .then(({ data }) => setDoctors(data))
      .catch(() => setDoctors([]));
  }, []);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
        const { data } = await api.get("/admin/appointments", { params });
        setAppointments(data);
      } catch (err) {
        setError(getApiError(err));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [filters]);

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  return (
    <Card>
      <CardHeader
        title="Manage Appointments"
        action={
          <div className="grid gap-2 sm:grid-cols-3">
            <Select value={filters.status} onChange={(event) => updateFilter("status", event.target.value)}>
              <option value="">All statuses</option>
              <option value="booked">Booked</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
              <option value="no_show">No show</option>
            </Select>
            <Select value={filters.doctor_id} onChange={(event) => updateFilter("doctor_id", event.target.value)}>
              <option value="">All doctors</option>
              {doctors.map((doctor) => (
                <option key={doctor.id} value={doctor.id}>
                  {doctor.full_name}
                </option>
              ))}
            </Select>
            <input
              type="date"
              value={filters.date}
              onChange={(event) => updateFilter("date", event.target.value)}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
            />
          </div>
        }
      />
      <CardBody>
        {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        {loading ? (
          <Loader label="Loading appointments" />
        ) : appointments.length === 0 ? (
          <EmptyState title="No appointments found" />
        ) : (
          <Table
            columns={["Patient", "Doctor", "Specialty", "Date and Time", "Urgency", "Status", "Symptoms"]}
            rows={appointments}
            renderRow={(appointment) => (
              <tr key={appointment.id}>
                <td className="px-4 py-3 font-medium text-gray-950">{appointment.patient_name}</td>
                <td className="px-4 py-3 text-gray-600">{appointment.doctor_name}</td>
                <td className="px-4 py-3 text-gray-600">{appointment.specialty}</td>
                <td className="px-4 py-3 text-gray-600">{formatDateTime(appointment.start_time)}</td>
                <td className="px-4 py-3">{appointment.urgency_level ? <UrgencyBadge level={appointment.urgency_level} /> : "N/A"}</td>
                <td className="px-4 py-3"><Badge>{appointment.status}</Badge></td>
                <td className="max-w-xs px-4 py-3 text-gray-600">{appointment.symptoms || "None"}</td>
              </tr>
            )}
          />
        )}
      </CardBody>
    </Card>
  );
}
