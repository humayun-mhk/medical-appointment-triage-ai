import { useEffect, useState } from "react";

import api, { getApiError } from "../../api/axios.js";
import Badge from "../../components/Badge.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import DoctorPortrait from "../../components/DoctorPortrait.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import Table from "../../components/Table.jsx";
import { formatCurrency } from "../../utils/format.js";

export default function ManageDoctors() {
  const [doctors, setDoctors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/admin/doctors")
      .then(({ data }) => setDoctors(data))
      .catch((err) => setError(getApiError(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader label="Loading doctors" />;

  return (
    <Card>
      <CardHeader title="Manage Doctors" />
      <CardBody>
        {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        {doctors.length === 0 ? (
          <EmptyState title="No doctors found" />
        ) : (
          <Table
            columns={["Doctor", "Email", "Specialty", "Experience", "Fee", "Availability"]}
            rows={doctors}
            renderRow={(doctor) => (
              <tr key={doctor.id}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <DoctorPortrait doctor={doctor} className="h-11 w-11" />
                    <span className="font-medium text-gray-950">{doctor.full_name}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-gray-600">{doctor.email}</td>
                <td className="px-4 py-3 text-gray-600">{doctor.specialty?.name}</td>
                <td className="px-4 py-3 text-gray-600">{doctor.experience_years} years</td>
                <td className="px-4 py-3 text-gray-600">{formatCurrency(doctor.consultation_fee)}</td>
                <td className="px-4 py-3"><Badge tone={doctor.is_available ? "available" : "cancelled"}>{doctor.is_available ? "available" : "inactive"}</Badge></td>
              </tr>
            )}
          />
        )}
      </CardBody>
    </Card>
  );
}
