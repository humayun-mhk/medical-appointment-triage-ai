import { useEffect, useMemo, useState } from "react";
import { Link, useLocation, useNavigate, useParams } from "react-router-dom";

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

const categories = [
  "specialty_description",
  "clinic_policy",
  "emergency_policy",
  "doctor_service",
  "faq",
  "cancellation_policy",
  "patient_preparation",
  "safety_guideline",
];

const blankForm = {
  title: "",
  category: "faq",
  source: "",
  content: "",
  metadataText: "{}",
  is_active: true,
};

function documentToForm(document) {
  return {
    title: document.title || "",
    category: document.category || "faq",
    source: document.source || "",
    content: document.content || "",
    metadataText: JSON.stringify(document.metadata || {}, null, 2),
    is_active: Boolean(document.is_active),
  };
}

export default function RagKnowledgeBase() {
  const { id } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const mode = useMemo(() => {
    if (location.pathname.endsWith("/new")) return "new";
    if (location.pathname.endsWith("/edit")) return "edit";
    if (id) return "detail";
    return "list";
  }, [id, location.pathname]);

  const [documents, setDocuments] = useState([]);
  const [document, setDocument] = useState(null);
  const [form, setForm] = useState(blankForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      if (mode === "list" || mode === "new") {
        const { data } = await adminStep3Api.knowledgeDocuments();
        setDocuments(data);
        if (mode === "new") setForm(blankForm);
      } else {
        const { data } = await adminStep3Api.knowledgeDocument(id);
        setDocument(data);
        setForm(documentToForm(data));
      }
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, [mode, id]);

  function updateField(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function payloadFromForm() {
    let metadata = {};
    try {
      metadata = JSON.parse(form.metadataText || "{}");
    } catch {
      throw new Error("Metadata must be valid JSON.");
    }
    return {
      title: form.title,
      category: form.category,
      source: form.source,
      content: form.content,
      metadata,
      is_active: form.is_active,
    };
  }

  async function save(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const payload = payloadFromForm();
      if (mode === "edit") {
        await adminStep3Api.updateKnowledgeDocument(id, payload);
        setSuccess("Knowledge document updated.");
        navigate(`/admin/knowledge-base/${id}`);
      } else {
        const { data } = await adminStep3Api.createKnowledgeDocument(payload);
        navigate(`/admin/knowledge-base/${data.id}`);
      }
    } catch (err) {
      setError(err.message || getApiError(err));
    } finally {
      setSaving(false);
    }
  }

  async function reindex() {
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const { data } = await adminStep3Api.reindexKnowledgeDocument(id);
      setDocument(data);
      setSuccess("Document reindexed.");
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setSaving(false);
    }
  }

  async function deactivate() {
    setSaving(true);
    setError("");
    try {
      await adminStep3Api.deleteKnowledgeDocument(id);
      setSuccess("Document deactivated.");
      await load();
    } catch (err) {
      setError(getApiError(err));
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <Loader label="Loading knowledge base" />;

  if (mode === "new" || mode === "edit") {
    return (
      <Card>
        <CardHeader title={mode === "new" ? "New Knowledge Document" : "Edit Knowledge Document"} />
        <CardBody>
          {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
          <form onSubmit={save} className="space-y-4">
            <Input label="Title" value={form.title} onChange={(event) => updateField("title", event.target.value)} required />
            <div className="grid gap-4 md:grid-cols-2">
              <Select value={form.category} onChange={(event) => updateField("category", event.target.value)}>
                {categories.map((category) => <option key={category} value={category}>{category.replaceAll("_", " ")}</option>)}
              </Select>
              <Input label="Source" value={form.source} onChange={(event) => updateField("source", event.target.value)} required />
            </div>
            <textarea
              value={form.content}
              onChange={(event) => updateField("content", event.target.value)}
              className="min-h-64 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
              placeholder="Document content"
              required
            />
            <textarea
              value={form.metadataText}
              onChange={(event) => updateField("metadataText", event.target.value)}
              className="min-h-28 w-full rounded-md border border-gray-300 px-3 py-2 font-mono text-xs focus:border-teal-500 focus:ring-2 focus:ring-teal-100"
              placeholder='{"source_type":"internal"}'
            />
            <label className="flex items-center gap-2 text-sm text-gray-700">
              <input type="checkbox" checked={form.is_active} onChange={(event) => updateField("is_active", event.target.checked)} />
              Active
            </label>
            <div className="flex gap-2">
              <Button type="submit" disabled={saving}>{saving ? "Saving..." : "Save Document"}</Button>
              <Link to={mode === "edit" ? `/admin/knowledge-base/${id}` : "/admin/knowledge-base"}>
                <Button type="button" variant="secondary">Cancel</Button>
              </Link>
            </div>
          </form>
        </CardBody>
      </Card>
    );
  }

  if (mode === "detail" && document) {
    return (
      <div className="space-y-6">
        <Card>
          <CardHeader
            title={document.title}
            description={`${document.source} - ${formatDateTime(document.updated_at)}`}
            action={
              <div className="flex flex-wrap gap-2">
                <Link to={`/admin/knowledge-base/${document.id}/edit`}><Button variant="secondary">Edit</Button></Link>
                <Button variant="secondary" onClick={reindex} disabled={saving}>Reindex</Button>
                <Button variant="danger" onClick={deactivate} disabled={saving}>Deactivate</Button>
              </div>
            }
          />
          <CardBody className="space-y-4">
            {error && <div className="rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
            {success && <div className="rounded-md bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{success}</div>}
            <div className="flex flex-wrap gap-2">
              <Badge tone={document.category}>{document.category}</Badge>
              <Badge tone={document.is_active ? "available" : "cancelled"}>{document.is_active ? "active" : "inactive"}</Badge>
              <Badge>{document.chunks_count} chunks</Badge>
            </div>
            <div className="whitespace-pre-wrap rounded-md bg-gray-50 p-4 text-sm text-gray-700">{document.content}</div>
            <pre className="overflow-auto rounded-md bg-gray-950 p-3 text-xs text-gray-50">{JSON.stringify(document.metadata, null, 2)}</pre>
          </CardBody>
        </Card>
        <Card>
          <CardHeader title="Chunks" />
          <CardBody>
            {document.chunks.length === 0 ? (
              <EmptyState title="No chunks indexed" />
            ) : (
              <div className="space-y-3">
                {document.chunks.map((chunk) => (
                  <div key={chunk.id} className="rounded-md border border-gray-200 p-3 text-sm text-gray-700">
                    <p className="mb-2 font-semibold text-gray-950">Chunk {chunk.chunk_index + 1}</p>
                    {chunk.chunk_text}
                  </div>
                ))}
              </div>
            )}
          </CardBody>
        </Card>
      </div>
    );
  }

  return (
    <Card>
      <CardHeader
        title="RAG Knowledge Base"
        description="Internal policy documents used only for routing and appointment guidance."
        action={<Link to="/admin/knowledge-base/new"><Button>New Document</Button></Link>}
      />
      <CardBody>
        {error && <div className="mb-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</div>}
        {documents.length === 0 ? (
          <EmptyState title="No knowledge documents found" />
        ) : (
          <Table
            columns={["Title", "Category", "Source", "Status", "Chunks", "Updated", "Action"]}
            rows={documents}
            renderRow={(item) => (
              <tr key={item.id}>
                <td className="px-4 py-3 font-medium text-gray-950">{item.title}</td>
                <td className="px-4 py-3"><Badge tone={item.category}>{item.category}</Badge></td>
                <td className="px-4 py-3 text-gray-600">{item.source}</td>
                <td className="px-4 py-3"><Badge tone={item.is_active ? "available" : "cancelled"}>{item.is_active ? "active" : "inactive"}</Badge></td>
                <td className="px-4 py-3 text-gray-600">{item.chunks_count}</td>
                <td className="px-4 py-3 text-gray-600">{formatDateTime(item.updated_at)}</td>
                <td className="px-4 py-3">
                  <Link to={`/admin/knowledge-base/${item.id}`}>
                    <Button variant="secondary">View</Button>
                  </Link>
                </td>
              </tr>
            )}
          />
        )}
      </CardBody>
    </Card>
  );
}
