import { useEffect, useState } from "react";

import { adminStep3Api } from "../../api/adminStep3Api.js";
import { getApiError } from "../../api/axios.js";
import Badge from "../../components/Badge.jsx";
import Button from "../../components/Button.jsx";
import Card, { CardBody, CardHeader } from "../../components/Card.jsx";
import EmptyState from "../../components/EmptyState.jsx";
import Input from "../../components/Input.jsx";
import Loader from "../../components/Loader.jsx";
import Select from "../../components/Select.jsx";
import Table from "../../components/Table.jsx";
import { formatDateTime } from "../../utils/format.js";

export default function NotificationLogs() {
  const [logs, setLogs] = useState([]);
  const [filters, setFilters] = useState({ channel: "", status: "", event_type: "", date: "" });
  const [testForm, setTestForm] = useState({ channel: "email", email: "", phone: "", message: "This is a test notification." });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const params = Object.fromEntries(Object.entries(filters).filter(([, value]) => value));
      const { data } = await adminStep3Api.notificationLogs(params);
      setLogs(data);
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [filters]);

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }

  function updateTest(key, value) {
    setTestForm((current) => ({ ...current, [key]: value }));
  }

  async function sendTest(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      await adminStep3Api.sendTestNotification(testForm);
      setSuccess("Test notification sent using configured provider or console fallback.");
      await load();
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader title="Test Notification" description="Provider keys are read only from backend environment variables." />
        <CardBody>
          {success && <div className="mb-4 rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{success}</div>}
          <form onSubmit={sendTest} className="grid gap-3 md:grid-cols-5">
            <Select value={testForm.channel} onChange={(event) => updateTest("channel", event.target.value)}>
              <option value="email">Email</option>
              <option value="sms">SMS</option>
              <option value="whatsapp">WhatsApp</option>
              <option value="in_app">In-app</option>
            </Select>
            <Input label="Email" value={testForm.email} onChange={(event) => updateTest("email", event.target.value)} />
            <Input label="Phone" value={testForm.phone} onChange={(event) => updateTest("phone", event.target.value)} />
            <Input label="Message" value={testForm.message} onChange={(event) => updateTest("message", event.target.value)} />
            <div className="flex items-end">
              <Button type="submit" disabled={saving}>{saving ? "Sending..." : "Send Test"}</Button>
            </div>
          </form>
        </CardBody>
      </Card>

      <Card>
        <CardHeader
          title="Notification Logs"
          action={
            <div className="grid gap-2 sm:grid-cols-4">
              <Select value={filters.channel} onChange={(event) => updateFilter("channel", event.target.value)}>
                <option value="">All channels</option>
                <option value="email">Email</option>
                <option value="sms">SMS</option>
                <option value="whatsapp">WhatsApp</option>
                <option value="in_app">In-app</option>
              </Select>
              <Select value={filters.status} onChange={(event) => updateFilter("status", event.target.value)}>
                <option value="">All status</option>
                <option value="sent">Sent</option>
                <option value="failed">Failed</option>
                <option value="pending">Pending</option>
              </Select>
              <Input label="Event" value={filters.event_type} onChange={(event) => updateFilter("event_type", event.target.value)} />
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
            <Loader label="Loading notification logs" />
          ) : logs.length === 0 ? (
            <EmptyState title="No notification logs found" />
          ) : (
            <Table
              columns={["Channel", "Event", "Recipient", "Status", "Provider", "Error", "Created", "Sent"]}
              rows={logs}
              renderRow={(log) => (
                <tr key={log.id}>
                  <td className="px-4 py-3"><Badge tone={log.channel}>{log.channel}</Badge></td>
                  <td className="px-4 py-3 text-gray-600">{log.event_type}</td>
                  <td className="px-4 py-3 text-gray-600">{log.recipient}</td>
                  <td className="px-4 py-3"><Badge tone={log.status}>{log.status}</Badge></td>
                  <td className="px-4 py-3 text-gray-600">{log.provider}</td>
                  <td className="max-w-sm px-4 py-3 text-rose-700">{log.error_message || "None"}</td>
                  <td className="px-4 py-3 text-gray-600">{formatDateTime(log.created_at)}</td>
                  <td className="px-4 py-3 text-gray-600">{formatDateTime(log.sent_at)}</td>
                </tr>
              )}
            />
          )}
        </CardBody>
      </Card>
    </div>
  );
}
