"""add ai triage workflow tables

Revision ID: 0002_add_ai_triage
Revises: 0001_initial_schema
Create Date: 2026-06-17 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0002_add_ai_triage"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


triage_urgency = postgresql.ENUM(
    "routine",
    "soon",
    "urgent",
    "emergency",
    name="triage_urgency",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    triage_urgency.create(bind, checkfirst=True)

    op.add_column("doctors", sa.Column("rating", sa.Float(), nullable=False, server_default="4.5"))
    op.add_column("doctors", sa.Column("total_reviews", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("doctors", sa.Column("city", sa.String(length=120), nullable=True))

    op.create_table(
        "symptom_sessions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("patient_id", sa.Integer(), nullable=False),
        sa.Column("raw_input", sa.Text(), nullable=False),
        sa.Column("structured_symptoms", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("red_flag_status", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("urgency_level", triage_urgency, nullable=False),
        sa.Column("recommended_specialty_id", sa.Integer(), nullable=True),
        sa.Column("secondary_specialty_id", sa.Integer(), nullable=True),
        sa.Column("ai_confidence", sa.Float(), nullable=True),
        sa.Column("ai_reason", sa.Text(), nullable=True),
        sa.Column("doctor_summary", sa.Text(), nullable=True),
        sa.Column("safety_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["patient_id"], ["patient_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recommended_specialty_id"], ["specialties.id"]),
        sa.ForeignKeyConstraint(["secondary_specialty_id"], ["specialties.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_symptom_sessions_id"), "symptom_sessions", ["id"], unique=False)
    op.create_index(op.f("ix_symptom_sessions_patient_id"), "symptom_sessions", ["patient_id"], unique=False)
    op.create_index(op.f("ix_symptom_sessions_urgency_level"), "symptom_sessions", ["urgency_level"], unique=False)
    op.create_index(
        op.f("ix_symptom_sessions_recommended_specialty_id"),
        "symptom_sessions",
        ["recommended_specialty_id"],
        unique=False,
    )

    op.create_table(
        "ai_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("agent_name", sa.String(length=120), nullable=False),
        sa.Column("input_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("output_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("safety_flags", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("model_name", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["symptom_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_ai_audit_logs_id"), "ai_audit_logs", ["id"], unique=False)
    op.create_index(op.f("ix_ai_audit_logs_session_id"), "ai_audit_logs", ["session_id"], unique=False)
    op.create_index(op.f("ix_ai_audit_logs_agent_name"), "ai_audit_logs", ["agent_name"], unique=False)
    op.create_index("ix_ai_audit_logs_session_agent", "ai_audit_logs", ["session_id", "agent_name"], unique=False)

    op.add_column("appointments", sa.Column("triage_session_id", sa.Integer(), nullable=True))
    op.add_column("appointments", sa.Column("doctor_summary", sa.Text(), nullable=True))
    op.create_index(op.f("ix_appointments_triage_session_id"), "appointments", ["triage_session_id"], unique=False)
    op.create_foreign_key(
        "fk_appointments_triage_session_id_symptom_sessions",
        "appointments",
        "symptom_sessions",
        ["triage_session_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.alter_column("doctors", "rating", server_default=None)
    op.alter_column("doctors", "total_reviews", server_default=None)


def downgrade() -> None:
    op.drop_constraint("fk_appointments_triage_session_id_symptom_sessions", "appointments", type_="foreignkey")
    op.drop_index(op.f("ix_appointments_triage_session_id"), table_name="appointments")
    op.drop_column("appointments", "doctor_summary")
    op.drop_column("appointments", "triage_session_id")

    op.drop_index("ix_ai_audit_logs_session_agent", table_name="ai_audit_logs")
    op.drop_index(op.f("ix_ai_audit_logs_agent_name"), table_name="ai_audit_logs")
    op.drop_index(op.f("ix_ai_audit_logs_session_id"), table_name="ai_audit_logs")
    op.drop_index(op.f("ix_ai_audit_logs_id"), table_name="ai_audit_logs")
    op.drop_table("ai_audit_logs")

    op.drop_index(op.f("ix_symptom_sessions_recommended_specialty_id"), table_name="symptom_sessions")
    op.drop_index(op.f("ix_symptom_sessions_urgency_level"), table_name="symptom_sessions")
    op.drop_index(op.f("ix_symptom_sessions_patient_id"), table_name="symptom_sessions")
    op.drop_index(op.f("ix_symptom_sessions_id"), table_name="symptom_sessions")
    op.drop_table("symptom_sessions")

    op.drop_column("doctors", "city")
    op.drop_column("doctors", "total_reviews")
    op.drop_column("doctors", "rating")

    bind = op.get_bind()
    triage_urgency.drop(bind, checkfirst=True)
