import { useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { adminStep3Api } from "../../api/adminStep3Api.js";
import { getApiError } from "../../api/axios.js";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Loader from "../../components/Loader.jsx";
import Table from "../../components/Table.jsx";

const COLORS = ["#0f766e", "#2563eb", "#f97316", "#dc2626", "#7c3aed"];

function Kpi({ label, value }) {
  return (
    <Card>
      <CardBody>
        <p className="text-sm font-medium text-gray-500">{label}</p>
        <p className="mt-2 text-3xl font-bold text-gray-950">{value ?? 0}</p>
      </CardBody>
    </Card>
  );
}

function ChartCard({ title, children }) {
  return (
    <Card>
      <CardHeader title={title} />
      <CardBody className="h-72">{children}</CardBody>
    </Card>
  );
}

export default function AnalyticsDashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [overview, symptoms, specialties, doctors, ai, notifications] = await Promise.all([
          adminStep3Api.analyticsOverview(),
          adminStep3Api.analyticsSymptoms(),
          adminStep3Api.analyticsSpecialties(),
          adminStep3Api.analyticsDoctors(),
          adminStep3Api.analyticsAi(),
          adminStep3Api.analyticsNotifications(),
        ]);
        setData({
          overview: overview.data,
          symptoms: symptoms.data,
          specialties: specialties.data,
          doctors: doctors.data,
          ai: ai.data,
          notifications: notifications.data,
        });
      } catch (err) {
        setError(getApiError(err));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <Loader label="Loading analytics" />;
  if (error) return <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>;
  if (!data) return <EmptyState title="No analytics available" />;

  const appointmentStatus = data.ai.appointment_status_distribution || [];
  const urgency = data.ai.triage_urgency_distribution || [];
  const notificationRows = [
    { name: "sent", count: data.notifications.sent },
    { name: "failed", count: data.notifications.failed },
    { name: "pending", count: data.notifications.pending },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-950">Analytics Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">Operational, AI safety, notification, and utilization metrics.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
        <Kpi label="Total appointments" value={data.overview.total_appointments} />
        <Kpi label="Today" value={data.overview.appointments_today} />
        <Kpi label="Urgent cases" value={data.overview.urgent_cases} />
        <Kpi label="Red flags" value={data.overview.red_flag_cases} />
        <Kpi label="Avg confidence" value={`${Math.round((data.overview.average_ai_confidence || 0) * 100)}%`} />
        <Kpi label="Pending reviews" value={data.overview.pending_review_cases} />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ChartCard title="Appointment Status">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={appointmentStatus} dataKey="count" nameKey="status" outerRadius={90} label>
                {appointmentStatus.map((entry, index) => <Cell key={entry.status} fill={COLORS[index % COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Triage Urgency">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={urgency}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="urgency" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#0f766e" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Most Common Symptoms">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.symptoms}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="symptom" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#2563eb" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Most Booked Specialties">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.specialties}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="specialty" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#f97316" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader title="Doctor Utilization" />
          <CardBody>
            <Table
              columns={["Doctor", "Slots", "Booked", "Utilization"]}
              rows={data.doctors}
              renderRow={(doctor) => (
                <tr key={doctor.doctor_id}>
                  <td className="px-4 py-3 font-medium text-gray-950">{doctor.doctor_name}</td>
                  <td className="px-4 py-3 text-gray-600">{doctor.total_slots}</td>
                  <td className="px-4 py-3 text-gray-600">{doctor.booked_slots}</td>
                  <td className="px-4 py-3 text-gray-600">{doctor.utilization_rate}%</td>
                </tr>
              )}
            />
          </CardBody>
        </Card>
        <ChartCard title="Notification Delivery">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={notificationRows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis allowDecimals={false} />
              <Tooltip />
              <Bar dataKey="count" fill="#7c3aed" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
}
