import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import api, { getApiError } from "../../api/axios.js";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";

export default function PatientSpecialties() {
  const [specialties, setSpecialties] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/specialties")
      .then(({ data }) => setSpecialties(data))
      .catch((err) => setError(getApiError(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader label="Loading specialties" />;

  return (
    <Card>
      <CardHeader title="Medical Specialties" description="Browse available departments." />
      <CardBody>
        {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        {specialties.length === 0 ? (
          <EmptyState title="No specialties available" />
        ) : (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {specialties.map((specialty) => (
              <div key={specialty.id} className="rounded-md border border-gray-200 p-4">
                <h2 className="font-semibold text-gray-950">{specialty.name}</h2>
                <p className="mt-2 min-h-12 text-sm leading-6 text-gray-600">{specialty.description || "No description added."}</p>
                <Link to={`/patient/doctors?specialty_id=${specialty.id}`}>
                  <Button variant="secondary" className="mt-4">
                    View Doctors
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
