"""add production ai platform features

Revision ID: 0003_production_ai_features
Revises: 0002_add_ai_triage
Create Date: 2026-06-17 00:00:02.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # pragma: no cover
    Vector = None


revision: str = "0003_production_ai_features"
down_revision: Union[str, None] = "0002_add_ai_triage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


knowledge_category = postgresql.ENUM(
    "specialty_description",
    "clinic_policy",
    "emergency_policy",
    "doctor_service",
    "faq",
    "cancellation_policy",
    "patient_preparation",
    "safety_guideline",
    name="knowledge_category",
    create_type=False,
)
review_risk_level = postgresql.ENUM("low", "medium", "high", "critical", name="review_risk_level", create_type=False)
review_status = postgresql.ENUM("pending", "in_review", "resolved", "dismissed", name="review_status", create_type=False)
notification_channel = postgresql.ENUM("email", "sms", "whatsapp", "in_app", name="notification_channel", create_type=False)
notification_status = postgresql.ENUM("pending", "sent", "failed", name="notification_status", create_type=False)
scheduled_job_status = postgresql.ENUM("pending", "completed", "failed", "cancelled", name="scheduled_job_status", create_type=False)


def _embedding_column() -> sa.Column:
    if Vector is None:
        return sa.Column("embedding", postgresql.JSONB(astext_type=sa.Text()), nullable=True)
    return sa.Column("embedding", Vector(384), nullable=True)


def upgrade() -> None:
    bind = op.get_bind()
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    knowledge_category.create(bind, checkfirst=True)
    review_risk_level.create(bind, checkfirst=True)
    review_status.create(bind, checkfirst=True)
    notification_channel.create(bind, checkfirst=True)
    notification_status.create(bind, checkfirst=True)
    scheduled_job_status.create(bind, checkfirst=True)

    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", knowledge_category, nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_documents_id"), "knowledge_documents", ["id"], unique=False)
    op.create_index(op.f("ix_knowledge_documents_category"), "knowledge_documents", ["category"], unique=False)
    op.create_index(op.f("ix_knowledge_documents_is_active"), "knowledge_documents", ["is_active"], unique=False)

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        _embedding_column(),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_knowledge_chunks_id"), "knowledge_chunks", ["id"], unique=False)
    op.create_index(op.f("ix_knowledge_chunks_document_id"), "knowledge_chunks", ["document_id"], unique=False)
    op.create_index("ix_knowledge_chunks_document_index", "knowledge_chunks", ["document_id", "chunk_index"], unique=True)
    if Vector is not None:
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_knowledge_chunks_embedding_hnsw "
            "ON knowledge_chunks USING hnsw (embedding vector_cosine_ops)"
        )

    op.create_table(
        "rag_queries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("triage_session_id", sa.Integer(), nullable=True),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("retrieved_chunks", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("response_text", sa.Text(), nullable=False),
        sa.Column("safety_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["triage_session_id"], ["symptom_sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_rag_queries_id"), "rag_queries", ["id"], unique=False)
    op.create_index(op.f("ix_rag_queries_user_id"), "rag_queries", ["user_id"], unique=False)
    op.create_index(op.f("ix_rag_queries_triage_session_id"), "rag_queries", ["triage_session_id"], unique=False)

    op.create_table(
        "human_review_cases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("triage_session_id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("assigned_admin_id", sa.Integer(), nullable=True),
        sa.Column("assigned_doctor_id", sa.Integer(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("risk_level", review_risk_level, nullable=False, server_default="medium"),
        sa.Column("status", review_status, nullable=False, server_default="pending"),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assigned_admin_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["assigned_doctor_id"], ["doctors.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["triage_session_id"], ["symptom_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_human_review_cases_id"), "human_review_cases", ["id"], unique=False)
    op.create_index(op.f("ix_human_review_cases_triage_session_id"), "human_review_cases", ["triage_session_id"], unique=False)
    op.create_index(op.f("ix_human_review_cases_patient_id"), "human_review_cases", ["patient_id"], unique=False)
    op.create_index(op.f("ix_human_review_cases_assigned_admin_id"), "human_review_cases", ["assigned_admin_id"], unique=False)
    op.create_index(op.f("ix_human_review_cases_assigned_doctor_id"), "human_review_cases", ["assigned_doctor_id"], unique=False)
    op.create_index(op.f("ix_human_review_cases_risk_level"), "human_review_cases", ["risk_level"], unique=False)
    op.create_index(op.f("ix_human_review_cases_status"), "human_review_cases", ["status"], unique=False)
    op.create_index("ix_human_review_cases_session_status", "human_review_cases", ["triage_session_id", "status"], unique=False)

    op.create_table(
        "notification_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("appointment_id", sa.Integer(), nullable=True),
        sa.Column("channel", notification_channel, nullable=False),
        sa.Column("event_type", sa.String(length=120), nullable=False),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("message_preview", sa.Text(), nullable=False),
        sa.Column("status", notification_status, nullable=False, server_default="pending"),
        sa.Column("provider", sa.String(length=80), nullable=False, server_default="console"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notification_logs_id"), "notification_logs", ["id"], unique=False)
    op.create_index(op.f("ix_notification_logs_user_id"), "notification_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_notification_logs_appointment_id"), "notification_logs", ["appointment_id"], unique=False)
    op.create_index(op.f("ix_notification_logs_channel"), "notification_logs", ["channel"], unique=False)
    op.create_index(op.f("ix_notification_logs_event_type"), "notification_logs", ["event_type"], unique=False)
    op.create_index(op.f("ix_notification_logs_status"), "notification_logs", ["status"], unique=False)
    op.create_index("ix_notification_logs_channel_status", "notification_logs", ["channel", "status"], unique=False)
    op.create_index("ix_notification_logs_event_created", "notification_logs", ["event_type", "created_at"], unique=False)

    op.create_table(
        "scheduled_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("job_type", sa.String(length=120), nullable=False),
        sa.Column("appointment_id", sa.Integer(), nullable=True),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", scheduled_job_status, nullable=False, server_default="pending"),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scheduled_jobs_id"), "scheduled_jobs", ["id"], unique=False)
    op.create_index(op.f("ix_scheduled_jobs_job_type"), "scheduled_jobs", ["job_type"], unique=False)
    op.create_index(op.f("ix_scheduled_jobs_appointment_id"), "scheduled_jobs", ["appointment_id"], unique=False)
    op.create_index(op.f("ix_scheduled_jobs_run_at"), "scheduled_jobs", ["run_at"], unique=False)
    op.create_index(op.f("ix_scheduled_jobs_status"), "scheduled_jobs", ["status"], unique=False)
    op.create_index("ix_scheduled_jobs_due", "scheduled_jobs", ["status", "run_at"], unique=False)

    op.create_table(
        "security_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=120), nullable=False),
        sa.Column("resource_id", sa.String(length=120), nullable=True),
        sa.Column("ip_address", sa.String(length=80), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_security_audit_logs_id"), "security_audit_logs", ["id"], unique=False)
    op.create_index(op.f("ix_security_audit_logs_user_id"), "security_audit_logs", ["user_id"], unique=False)
    op.create_index(op.f("ix_security_audit_logs_action"), "security_audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_security_audit_logs_resource_type"), "security_audit_logs", ["resource_type"], unique=False)
    op.create_index(op.f("ix_security_audit_logs_resource_id"), "security_audit_logs", ["resource_id"], unique=False)
    op.create_index(op.f("ix_security_audit_logs_ip_address"), "security_audit_logs", ["ip_address"], unique=False)
    op.create_index("ix_security_audit_logs_action_created", "security_audit_logs", ["action", "created_at"], unique=False)
    op.create_index("ix_security_audit_logs_resource", "security_audit_logs", ["resource_type", "resource_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_security_audit_logs_resource", table_name="security_audit_logs")
    op.drop_index("ix_security_audit_logs_action_created", table_name="security_audit_logs")
    op.drop_index(op.f("ix_security_audit_logs_ip_address"), table_name="security_audit_logs")
    op.drop_index(op.f("ix_security_audit_logs_resource_id"), table_name="security_audit_logs")
    op.drop_index(op.f("ix_security_audit_logs_resource_type"), table_name="security_audit_logs")
    op.drop_index(op.f("ix_security_audit_logs_action"), table_name="security_audit_logs")
    op.drop_index(op.f("ix_security_audit_logs_user_id"), table_name="security_audit_logs")
    op.drop_index(op.f("ix_security_audit_logs_id"), table_name="security_audit_logs")
    op.drop_table("security_audit_logs")

    op.drop_index("ix_scheduled_jobs_due", table_name="scheduled_jobs")
    op.drop_index(op.f("ix_scheduled_jobs_status"), table_name="scheduled_jobs")
    op.drop_index(op.f("ix_scheduled_jobs_run_at"), table_name="scheduled_jobs")
    op.drop_index(op.f("ix_scheduled_jobs_appointment_id"), table_name="scheduled_jobs")
    op.drop_index(op.f("ix_scheduled_jobs_job_type"), table_name="scheduled_jobs")
    op.drop_index(op.f("ix_scheduled_jobs_id"), table_name="scheduled_jobs")
    op.drop_table("scheduled_jobs")

    op.drop_index("ix_notification_logs_event_created", table_name="notification_logs")
    op.drop_index("ix_notification_logs_channel_status", table_name="notification_logs")
    op.drop_index(op.f("ix_notification_logs_status"), table_name="notification_logs")
    op.drop_index(op.f("ix_notification_logs_event_type"), table_name="notification_logs")
    op.drop_index(op.f("ix_notification_logs_channel"), table_name="notification_logs")
    op.drop_index(op.f("ix_notification_logs_appointment_id"), table_name="notification_logs")
    op.drop_index(op.f("ix_notification_logs_user_id"), table_name="notification_logs")
    op.drop_index(op.f("ix_notification_logs_id"), table_name="notification_logs")
    op.drop_table("notification_logs")

    op.drop_index("ix_human_review_cases_session_status", table_name="human_review_cases")
    op.drop_index(op.f("ix_human_review_cases_status"), table_name="human_review_cases")
    op.drop_index(op.f("ix_human_review_cases_risk_level"), table_name="human_review_cases")
    op.drop_index(op.f("ix_human_review_cases_assigned_doctor_id"), table_name="human_review_cases")
    op.drop_index(op.f("ix_human_review_cases_assigned_admin_id"), table_name="human_review_cases")
    op.drop_index(op.f("ix_human_review_cases_patient_id"), table_name="human_review_cases")
    op.drop_index(op.f("ix_human_review_cases_triage_session_id"), table_name="human_review_cases")
    op.drop_index(op.f("ix_human_review_cases_id"), table_name="human_review_cases")
    op.drop_table("human_review_cases")

    op.drop_index(op.f("ix_rag_queries_triage_session_id"), table_name="rag_queries")
    op.drop_index(op.f("ix_rag_queries_user_id"), table_name="rag_queries")
    op.drop_index(op.f("ix_rag_queries_id"), table_name="rag_queries")
    op.drop_table("rag_queries")

    if Vector is not None:
        op.execute("DROP INDEX IF EXISTS ix_knowledge_chunks_embedding_hnsw")
    op.drop_index("ix_knowledge_chunks_document_index", table_name="knowledge_chunks")
    op.drop_index(op.f("ix_knowledge_chunks_document_id"), table_name="knowledge_chunks")
    op.drop_index(op.f("ix_knowledge_chunks_id"), table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")

    op.drop_index(op.f("ix_knowledge_documents_is_active"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_category"), table_name="knowledge_documents")
    op.drop_index(op.f("ix_knowledge_documents_id"), table_name="knowledge_documents")
    op.drop_table("knowledge_documents")

    bind = op.get_bind()
    scheduled_job_status.drop(bind, checkfirst=True)
    notification_status.drop(bind, checkfirst=True)
    notification_channel.drop(bind, checkfirst=True)
    review_status.drop(bind, checkfirst=True)
    review_risk_level.drop(bind, checkfirst=True)
    knowledge_category.drop(bind, checkfirst=True)
