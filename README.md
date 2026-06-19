# AI Healthcare Appointment & Safe Triage Platform

A production-style healthcare appointment system with AI triage, safe specialty routing, RAG-based policy knowledge, doctor dashboards, admin analytics, notifications, human review, and audit logs.

## Medical Safety Disclaimer

This system does not diagnose disease, prescribe medicine, provide treatment plans, or replace qualified doctors. It only supports symptom intake, urgency detection, safe doctor specialty routing, appointment workflow, doctor-facing summaries, and policy-based guidance. Emergency symptoms trigger an emergency-care warning.

## Features

- Patient registration/login, profiles, doctor browsing, appointment booking, history, and cancellation
- Doctor dashboard, appointment details, doctor notes, status updates, and availability management
- Admin dashboard, specialty/doctor/slot/patient/appointment management
- AI symptom intake with structured symptom extraction
- Rule-based red flag detection and urgency classification
- Specialty routing and doctor matching with score breakdown
- Triage-based booking with doctor-facing summary copied to appointments
- RAG knowledge base for routing, clinic policy, cancellation, preparation, FAQ, and emergency policy
- Human review queue for emergency, low-confidence, pregnancy, child/elderly, severe, or unsafe cases
- Email/SMS/WhatsApp/in-app notification service with console fallback
- Appointment reminder scheduler
- Analytics dashboard for operations, AI safety, doctors, and notifications
- AI audit logs, security audit logs, PII masking, role-based access control, rate limiting, and secure headers
- PostgreSQL + pgvector-ready deployment configuration

## Architecture

```text
Patient
  -> React Frontend
  -> FastAPI Backend
  -> PostgreSQL + pgvector
  -> AI Triage + RAG + Safety Engine
  -> Doctor Matching + Appointment Booking
  -> Notifications + Analytics + Audit Logs
```

## Tech Stack

Frontend: React, Vite, Tailwind CSS, Axios, React Router, React Hook Form, Zod, Recharts.

Backend: FastAPI, PostgreSQL, SQLAlchemy, Alembic, JWT, bcrypt, pgvector, optional OpenAI, APScheduler, optional SendGrid/Twilio.

## Folder Structure

```text
healthcare-appointment-system/
├── backend/
│   ├── app/
│   │   ├── ai/
│   │   ├── analytics/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── models/
│   │   ├── notifications/
│   │   ├── rag/
│   │   ├── review/
│   │   ├── schemas/
│   │   ├── security/
│   │   └── services/
│   ├── alembic/
│   ├── knowledge_base/
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── routes/
│   │   └── utils/
│   ├── vercel.json
│   ├── package.json
│   └── .env.example
├── docker-compose.yml
└── render.yaml
```

## Local Setup With Neon PostgreSQL

Create a Neon PostgreSQL project, enable pgvector in the database, and copy the Neon connection string. Use the direct URL or pooled URL Neon provides, keeping `sslmode=require`.

Backend:

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# edit backend/.env and set DATABASE_URL to your Neon URL
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

API: `http://localhost:8000`

Frontend: `http://localhost:5173`

Optional local PostgreSQL fallback:

```bash
docker compose up -d postgres
```

The Docker fallback maps PostgreSQL to host port `5433`.

## Environment Variables

Backend:

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST.neon.tech/DBNAME?sslmode=require
DB_POOL_PRE_PING=false
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_POOL_RECYCLE_SECONDS=1800
JWT_SECRET_KEY=change-this-secret-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
FRONTEND_URL=http://localhost:5173
OPENAI_API_KEY=
AI_MODEL=gpt-4o-mini
AI_PROVIDER=openai
TRIAGE_USE_LLM=true
TRIAGE_FALLBACK_RULES=true
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=text-embedding-3-small
EMAIL_PROVIDER=smtp
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_FROM_NAME=Healthcare Appointments
SMTP_USE_TLS=true
SMTP_TIMEOUT_SECONDS=10
SENDGRID_API_KEY=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
TWILIO_WHATSAPP_NUMBER=
```

Frontend:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Database and pgvector

The project uses Alembic migrations:

```bash
cd backend
alembic upgrade head
alembic downgrade -1
```

For Neon, run this once in the Neon SQL editor if the extension is not already enabled:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Migration `0003_production_ai_features` also attempts to enable pgvector and creates the RAG tables.

Seed users, doctors, slots, specialties, and knowledge-base documents:

```bash
python -m app.db.seed
```

You can seed only the knowledge base with:

```bash
python -m app.rag.seed_knowledge_base
```

## Test Accounts

| Role | Email | Password |
| --- | --- | --- |
| Admin | admin@healthcare.local | Admin123! |
| Patient | patient@healthcare.local | Patient123! |
| Doctor | doctor@healthcare.local | Doctor123! |
| Doctor | cardio@healthcare.local | Doctor123! |
| Doctor | ent@healthcare.local | Doctor123! |
| Doctor | derm@healthcare.local | Doctor123! |
| Doctor | gastro@healthcare.local | Doctor123! |
| Doctor | eye@healthcare.local | Doctor123! |

## API Summary

Auth: `POST /auth/register`, `POST /auth/login`, `GET /auth/me`

Patient: `GET /specialties`, `GET /doctors`, `POST /patients/profile`, `POST /appointments/book`, `GET /appointments/my`, `POST /appointments/{id}/cancel`

Doctor: `GET /doctor/appointments`, `GET /doctor/appointments/{id}`, `POST /doctor/appointments/{id}/notes`, `POST /doctor/appointments/{id}/status`, `GET/POST /doctor/availability`

Admin: `/admin/dashboard`, `/admin/specialties`, `/admin/doctors`, `/admin/slots`, `/admin/patients`, `/admin/appointments`

Triage: `POST /triage/start`, `POST /triage/analyze`, `GET /triage/result/{session_id}`, `GET /doctors/recommended/{session_id}`, `POST /appointments/book-from-triage`

RAG: `POST /rag/query`, `GET/POST /admin/knowledge-base`, `GET/PATCH/DELETE /admin/knowledge-base/{id}`, `POST /admin/knowledge-base/{id}/reindex`

Review: `GET /admin/review-cases`, `GET /admin/review-cases/{id}`, `PATCH /admin/review-cases/{id}/assign`, `PATCH /admin/review-cases/{id}/status`

Notifications: `GET /notifications/my`, `PATCH /notifications/{id}/read`, `PATCH /notifications/read-all`, `GET /admin/notification-logs`, `POST /admin/notifications/test`

Analytics: `GET /admin/analytics/overview`, `/symptoms`, `/specialties`, `/doctors`, `/ai`, `/notifications`

Audit: `GET /admin/ai-audit-logs`, `GET /admin/security-audit-logs`

## Safety Model

- Red flag detection is rule-based first because emergency routing should not depend on free-form AI output.
- RAG is limited to internal clinic/routing/policy documents.
- RAG refuses diagnosis, medicine, dosage, treatment, or false reassurance requests.
- Emergency cases force emergency urgency and create human review cases.
- Low-confidence, pregnancy-related, severe, child, elderly, and unsafe outputs can be flagged for human review.
- Doctor-facing summaries remain short, clinical, and non-diagnostic.

## Testing

Backend:

```bash
cd backend
pytest
```

Frontend:

```bash
cd frontend
npm run build
```

Manual checklist:

- Patient registers, logs in, completes profile, runs triage, reviews safe result, views recommended doctors, books, receives notification, cancels.
- Doctor logs in, sees assigned appointments only, reviews AI summary, adds notes, updates status.
- Admin views analytics, triage sessions, review queue, RAG knowledge base, notification logs, security audit logs, and resolves review cases.

## Deployment

Backend deployment target: Render or Railway using `backend/Dockerfile`.

Backend start command:

```bash
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Frontend deployment target: Vercel using `frontend/vercel.json`.

Frontend build command:

```bash
npm run build
```

Database target: Neon or Supabase PostgreSQL with pgvector enabled.

Set production CORS with:

```env
FRONTEND_URL=https://your-vercel-app.vercel.app
CORS_ORIGINS=https://your-vercel-app.vercel.app
```

Use HTTPS in production and store all provider keys only in backend environment variables.

For Brevo SMTP, set:

```env
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp-relay.brevo.com
SMTP_PORT=587
SMTP_USER=your-brevo-smtp-login
SMTP_PASSWORD=your-brevo-smtp-key
SMTP_FROM_EMAIL=your-verified-brevo-sender@example.com
SMTP_FROM_NAME=Healthcare Appointments
SMTP_USE_TLS=true
SMTP_TIMEOUT_SECONDS=10
```

## Screenshots

- Patient triage
- Recommended doctors
- Doctor dashboard
- Admin analytics
- Human review queue
- RAG knowledge base
- Security audit logs

## Interview Talking Points

- Rule-based emergency red flag detection is safer than pure LLM triage.
- RAG is limited to policy and routing knowledge, not diagnosis.
- Audit logs and retrieved chunks improve traceability.
- Human review reduces AI risk for low-confidence or high-risk cases.
- Doctor-only appointment access protects patient privacy.
- Analytics helps admins monitor utilization, safety, and operations.
- Emergency cases are routed to immediate care instead of routine booking.
