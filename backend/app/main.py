from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, analytics, auth, doctor, notifications, patient, public, rag, review, security, triage
from app.core.config import settings
from app.db.database import warm_database_pool
from app.notifications.reminder_scheduler import start_scheduler
from app.security.headers import SecurityHeadersMiddleware

app = FastAPI(title=settings.APP_NAME, version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(SecurityHeadersMiddleware)

app.include_router(auth.router)
app.include_router(public.router)
app.include_router(patient.router)
app.include_router(doctor.router)
app.include_router(admin.router)
app.include_router(triage.router)
app.include_router(rag.router)
app.include_router(review.router)
app.include_router(notifications.router)
app.include_router(analytics.router)
app.include_router(security.router)


@app.on_event("startup")
def startup_event():
    warm_database_pool()
    start_scheduler()


@app.get("/")
def root():
    return {"message": "AI Healthcare Appointment & Safe Triage Platform API", "version": "3.0.0"}
