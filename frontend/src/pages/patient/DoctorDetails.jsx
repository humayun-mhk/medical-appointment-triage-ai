import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import api, { getApiError } from "../../api/axios.js";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import DoctorPortrait from "../../components/DoctorPortrait.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import { formatCurrency, formatDateTime } from "../../utils/format.js";

export default function PatientDoctorDetails() {
  const { doctorId } = useParams();
  const [doctor, setDoctor] = useState(null);
  const [slots, setSlots] = useState([]);
  const [selectedDate, setSelectedDate] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDoctor() {
      try {
        const { data } = await api.get(`/doctors/${doctorId}`);
        setDoctor(data);
      } catch (err) {
        setError(getApiError(err));
      } finally {
        setLoading(false);
      }
    }
    loadDoctor();
  }, [doctorId]);

  useEffect(() => {
    async function loadSlots() {
      try {
        const { data } = await api.get(`/doctors/${doctorId}/slots`, {
          params: selectedDate ? { date: selectedDate } : {},
        });
        setSlots(data);
      } catch (err) {
        setError(getApiError(err));
      }
    }
    loadSlots();
  }, [doctorId, selectedDate]);

  if (loading) return <Loader label="Loading doctor details" />;

  if (!doctor) {
    return <EmptyState title="Doctor not found" message={error} />;
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <Card>
        <CardHeader
          title={doctor.full_name}
          description={doctor.specialty?.name}
          action={<DoctorPortrait doctor={doctor} className="h-24 w-24" />}
        />
        <CardBody className="space-y-3 text-sm text-gray-600">
          {error && <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
          <p><span className="font-semibold text-gray-800">Qualification:</span> {doctor.qualification}</p>
          <p><span className="font-semibold text-gray-800">Experience:</span> {doctor.experience_years} years</p>
          <p><span className="font-semibold text-gray-800">Fee:</span> {formatCurrency(doctor.consultation_fee)}</p>
          <p><span className="font-semibold text-gray-800">Clinic:</span> {doctor.clinic_address}</p>
          <p className="leading-6">{doctor.bio || "No bio added."}</p>
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title="Available Slots"
          action={
            <input
              type="date"
              value={selectedDate}
              onChange={(event) => setSelectedDate(event.target.value)}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
            />
          }
        />
        <CardBody>
          {slots.length === 0 ? (
            <EmptyState title="No slots available" message="Try a different date or check back later." />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {slots.map((slot) => (
                <div key={slot.id} className="rounded-md border border-gray-200 p-4">
                  <p className="font-semibold text-gray-950">{formatDateTime(slot.start_time)}</p>
                  <p className="mt-1 text-sm text-gray-500">Ends {formatDateTime(slot.end_time)}</p>
                  <Link to={`/patient/doctors/${doctor.id}/book?slot_id=${slot.id}`}>
                    <Button className="mt-4 w-full">Book Appointment</Button>
                  </Link>
                </div>
              ))}
            </div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
