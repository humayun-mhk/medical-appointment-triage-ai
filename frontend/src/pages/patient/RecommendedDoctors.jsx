import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { getApiError } from "../../api/axios.js";
import { triageApi } from "../../api/triageApi.js";
import DoctorRecommendationCard from "../../components/DoctorRecommendationCard.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import RedFlagAlert from "../../components/RedFlagAlert.jsx";

export default function RecommendedDoctors() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const [doctors, setDoctors] = useState([]);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [bookingId, setBookingId] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const [resultResponse, doctorResponse] = await Promise.all([
          triageApi.getResult(sessionId),
          triageApi.getRecommendedDoctors(sessionId),
        ]);
        setResult(resultResponse.data);
        setDoctors(doctorResponse.data);
      } catch (err) {
        setError(getApiError(err));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [sessionId]);

  async function book(recommendation) {
    setBookingId(recommendation.doctor_id);
    setError("");
    try {
      await triageApi.bookFromTriage({
        session_id: Number(sessionId),
        doctor_id: recommendation.doctor_id,
        slot_id: recommendation.next_available_slot.slot_id,
        patient_notes: "Booked from AI triage routing result.",
      });
      navigate("/patient/appointments", { replace: true });
    } catch (err) {
      setError(getApiError(err, "Unable to book appointment"));
    } finally {
      setBookingId(null);
    }
  }

  if (loading) return <Loader label="Loading recommended doctors" />;

  return (
    <div className="space-y-5">
      <RedFlagAlert show={result?.red_flag_status || result?.urgency_level === "emergency"} message={result?.safety_message} />
      {error && <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
      <div>
        <h1 className="text-2xl font-bold text-gray-950">Recommended Doctors</h1>
        <p className="mt-1 text-sm text-gray-500">Recommendations are based on specialty routing and available slots.</p>
      </div>
      {doctors.length === 0 ? (
        <EmptyState title="No matching doctors with available slots" message="Please try browsing doctors directly or contact the clinic." />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {doctors.map((doctor) => (
            <DoctorRecommendationCard
              key={doctor.doctor_id}
              recommendation={doctor}
              onBook={book}
              isBooking={bookingId === doctor.doctor_id}
            />
          ))}
        </div>
      )}
    </div>
  );
}
