import { useEffect, useState } from "react";

import api, { getApiError } from "../../api/axios.js";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import Table from "../../components/Table.jsx";

export default function ManagePatients() {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/admin/patients")
      .then(({ data }) => setPatients(data))
      .catch((err) => setError(getApiError(err)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loader label="Loading patients" />;

  return (
    <Card>
      <CardHeader title="Manage Patients" />
      <CardBody>
        {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        {patients.length === 0 ? (
          <EmptyState title="No patient profiles found" />
        ) : (
          <Table
            columns={["Patient", "Email", "Phone", "Gender", "Blood Group"]}
            rows={patients}
            renderRow={(patient) => (
              <tr key={patient.id}>
                <td className="px-4 py-3 font-medium text-gray-950">{patient.full_name}</td>
                <td className="px-4 py-3 text-gray-600">{patient.email}</td>
                <td className="px-4 py-3 text-gray-600">{patient.phone || "Not set"}</td>
                <td className="px-4 py-3 text-gray-600">{patient.gender || "Not set"}</td>
                <td className="px-4 py-3 text-gray-600">{patient.blood_group || "Not set"}</td>
              </tr>
            )}
          />
        )}
      </CardBody>
    </Card>
  );
}
