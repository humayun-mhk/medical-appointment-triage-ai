import { Navigate, Route, Routes } from "react-router-dom";

import ProtectedRoute from "../components/ProtectedRoute.jsx";
import RoleRoute from "../components/RoleRoute.jsx";
import AdminLayout from "../layouts/AdminLayout.jsx";
import DoctorLayout from "../layouts/DoctorLayout.jsx";
import PatientLayout from "../layouts/PatientLayout.jsx";
import AdminAppointments from "../pages/admin/Appointments.jsx";
import AdminDashboard from "../pages/admin/Dashboard.jsx";
import AddDoctor from "../pages/admin/AddDoctor.jsx";
import AddSpecialty from "../pages/admin/AddSpecialty.jsx";
import AIAuditLogs from "../pages/admin/AIAuditLogs.jsx";
import AnalyticsDashboard from "../pages/admin/AnalyticsDashboard.jsx";
import CreateSlots from "../pages/admin/CreateSlots.jsx";
import HumanReviewQueue from "../pages/admin/HumanReviewQueue.jsx";
import ManageDoctors from "../pages/admin/Doctors.jsx";
import ManagePatients from "../pages/admin/Patients.jsx";
import NotificationLogs from "../pages/admin/NotificationLogs.jsx";
import RagKnowledgeBase from "../pages/admin/RagKnowledgeBase.jsx";
import ReviewCaseDetails from "../pages/admin/ReviewCaseDetails.jsx";
import SecurityAuditLogs from "../pages/admin/SecurityAuditLogs.jsx";
import AdminTriageSessionDetail from "../pages/admin/TriageSessionDetail.jsx";
import AdminTriageSessions from "../pages/admin/TriageSessions.jsx";
import Login from "../pages/auth/Login.jsx";
import Register from "../pages/auth/Register.jsx";
import DoctorAppointmentDetails from "../pages/doctor/AppointmentDetails.jsx";
import DoctorAvailability from "../pages/doctor/Availability.jsx";
import DoctorDashboard from "../pages/doctor/Dashboard.jsx";
import TodayAppointments from "../pages/doctor/TodayAppointments.jsx";
import Home from "../pages/Home.jsx";
import PatientAppointments from "../pages/patient/Appointments.jsx";
import PatientBookAppointment from "../pages/patient/BookAppointment.jsx";
import PatientDashboard from "../pages/patient/Dashboard.jsx";
import PatientDoctorDetails from "../pages/patient/DoctorDetails.jsx";
import PatientDoctors from "../pages/patient/Doctors.jsx";
import PatientProfile from "../pages/patient/Profile.jsx";
import RecommendedDoctors from "../pages/patient/RecommendedDoctors.jsx";
import PatientSpecialties from "../pages/patient/Specialties.jsx";
import SymptomTriage from "../pages/patient/SymptomTriage.jsx";
import TriageResult from "../pages/patient/TriageResult.jsx";

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<RoleRoute roles={["patient"]} />}>
          <Route path="/patient" element={<PatientLayout />}>
            <Route index element={<Navigate to="/patient/dashboard" replace />} />
            <Route path="dashboard" element={<PatientDashboard />} />
            <Route path="profile" element={<PatientProfile />} />
            <Route path="triage" element={<SymptomTriage />} />
            <Route path="triage/:sessionId/result" element={<TriageResult />} />
            <Route path="triage/:sessionId/doctors" element={<RecommendedDoctors />} />
            <Route path="specialties" element={<PatientSpecialties />} />
            <Route path="doctors" element={<PatientDoctors />} />
            <Route path="doctors/:doctorId" element={<PatientDoctorDetails />} />
            <Route path="doctors/:doctorId/book" element={<PatientBookAppointment />} />
            <Route path="appointments" element={<PatientAppointments />} />
          </Route>
        </Route>

        <Route element={<RoleRoute roles={["doctor"]} />}>
          <Route path="/doctor" element={<DoctorLayout />}>
            <Route index element={<Navigate to="/doctor/dashboard" replace />} />
            <Route path="dashboard" element={<DoctorDashboard />} />
            <Route path="today" element={<TodayAppointments />} />
            <Route path="appointments/:appointmentId" element={<DoctorAppointmentDetails />} />
            <Route path="availability" element={<DoctorAvailability />} />
          </Route>
        </Route>

        <Route element={<RoleRoute roles={["admin"]} />}>
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<Navigate to="/admin/dashboard" replace />} />
            <Route path="dashboard" element={<AdminDashboard />} />
            <Route path="analytics" element={<AnalyticsDashboard />} />
            <Route path="specialties/new" element={<AddSpecialty />} />
            <Route path="doctors/new" element={<AddDoctor />} />
            <Route path="slots/new" element={<CreateSlots />} />
            <Route path="doctors" element={<ManageDoctors />} />
            <Route path="patients" element={<ManagePatients />} />
            <Route path="appointments" element={<AdminAppointments />} />
            <Route path="triage-sessions" element={<AdminTriageSessions />} />
            <Route path="triage-sessions/:sessionId" element={<AdminTriageSessionDetail />} />
            <Route path="review-cases" element={<HumanReviewQueue />} />
            <Route path="review-cases/:caseId" element={<ReviewCaseDetails />} />
            <Route path="knowledge-base" element={<RagKnowledgeBase />} />
            <Route path="knowledge-base/new" element={<RagKnowledgeBase />} />
            <Route path="knowledge-base/:id" element={<RagKnowledgeBase />} />
            <Route path="knowledge-base/:id/edit" element={<RagKnowledgeBase />} />
            <Route path="notification-logs" element={<NotificationLogs />} />
            <Route path="ai-audit-logs" element={<AIAuditLogs />} />
            <Route path="security-audit-logs" element={<SecurityAuditLogs />} />
          </Route>
        </Route>
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
