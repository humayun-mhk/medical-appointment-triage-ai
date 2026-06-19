import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import api, { getApiError } from "../../api/axios.js";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import DoctorPortrait from "../../components/DoctorPortrait.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import Select from "../../components/Select.jsx";
import { formatCurrency } from "../../utils/format.js";

export default function PatientDoctors() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [specialties, setSpecialties] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [symptomQuery, setSymptomQuery] = useState("");
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [recommending, setRecommending] = useState(false);
  const [error, setError] = useState("");
  const specialtyId = searchParams.get("specialty_id") || "";

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [specialtyResponse, doctorResponse] = await Promise.all([
          api.get("/specialties"),
          api.get("/doctors", { params: specialtyId ? { specialty_id: specialtyId } : {} }),
        ]);
        setSpecialties(specialtyResponse.data);
        setDoctors(doctorResponse.data);
        setRecommendation(null);
      } catch (err) {
        setError(getApiError(err));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [specialtyId]);

  if (loading) return <Loader label="Loading doctors" />;

  async function recommendDoctors(event) {
    event.preventDefault();
    const cleaned = symptomQuery.trim();
    if (!cleaned) return;
    setRecommending(true);
    setError("");
    try {
      const { data } = await api.get("/doctors/recommend", { params: { symptoms: cleaned } });
      setDoctors(data.doctors || []);
      setRecommendation(data);
    } catch (err) {
      setError(getApiError(err, "Unable to recommend doctors"));
    } finally {
      setRecommending(false);
    }
  }

  async function clearRecommendation() {
    setSymptomQuery("");
    setRecommendation(null);
    setSearchParams({});
  }

  return (
    <Card>
      <CardHeader
        title="Doctors"
        description="Find a doctor by specialty and view available appointment slots."
        action={
          <Select
            aria-label="Filter by specialty"
            value={specialtyId}
            onChange={(event) => {
              const value = event.target.value;
              setSearchParams(value ? { specialty_id: value } : {});
            }}
          >
            <option value="">All specialties</option>
            {specialties.map((specialty) => (
              <option key={specialty.id} value={specialty.id}>
                {specialty.name}
              </option>
            ))}
          </Select>
        }
      />
      <CardBody>
        {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        <form onSubmit={recommendDoctors} className="mb-5 rounded-md border border-gray-200 bg-gray-50 p-4">
          <label className="block">
            <span className="mb-1 block text-sm font-medium text-gray-700">Recommend by symptoms</span>
            <textarea
              value={symptomQuery}
              onChange={(event) => setSymptomQuery(event.target.value)}
              className="min-h-20 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm outline-none focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
              placeholder="Example: eye pain, blurry vision, red eye"
            />
          </label>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button type="submit" isLoading={recommending}>Recommend Doctors</Button>
            {recommendation && <Button type="button" variant="secondary" onClick={clearRecommendation}>Clear</Button>}
          </div>
          {recommendation && (
            <div className="mt-3 rounded-md bg-teal-50 px-3 py-2 text-sm text-teal-800">
              Recommended specialty: <span className="font-semibold">{recommendation.recommended_specialty?.name || "General Physician"}</span>
              {recommendation.red_flag_status && <span className="ml-2 font-semibold text-rose-700">Emergency warning active</span>}
              <p className="mt-1 text-teal-700">{recommendation.reason}</p>
            </div>
          )}
        </form>
        {doctors.length === 0 ? (
          <EmptyState title="No doctors found" message="Try another specialty filter." />
        ) : (
          <div className="grid gap-4 lg:grid-cols-2">
            {doctors.map((doctor) => (
              <div key={doctor.id} className="rounded-md border border-gray-200 p-4">
                <div className="flex gap-4">
                  <DoctorPortrait doctor={doctor} className="h-24 w-24" />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                      <div>
                        <h2 className="text-lg font-semibold text-gray-950">{doctor.full_name}</h2>
                        <p className="text-sm font-medium text-teal-700">{doctor.specialty?.name}</p>
                      </div>
                      <p className="w-fit rounded-md bg-gray-100 px-3 py-1 text-sm font-semibold text-gray-800">
                        {formatCurrency(doctor.consultation_fee)}
                      </p>
                    </div>
                    <p className="mt-3 text-sm text-gray-600">{doctor.qualification}</p>
                    <p className="mt-1 text-sm text-gray-600">{doctor.experience_years} years experience</p>
                    <p className="mt-1 text-sm text-gray-600">{doctor.clinic_address}</p>
                    <Link to={`/patient/doctors/${doctor.id}`}>
                      <Button className="mt-4">View Details</Button>
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
