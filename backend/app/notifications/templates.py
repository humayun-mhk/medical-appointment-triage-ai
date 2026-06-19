from html import escape


def _format_time(value) -> str:
    return value.strftime("%A, %B %d, %Y at %I:%M %p") if value else "Scheduled time"


def appointment_booked_patient(appointment) -> tuple[str, str]:
    appointment_time = _format_time(appointment.slot.start_time)
    return (
        "Appointment confirmation",
        (
            f"Hello {appointment.patient.user.full_name},\n\n"
            f"Your appointment is confirmed with {appointment.doctor.user.full_name} "
            f"({appointment.doctor.specialty.name}) on {appointment_time}.\n"
            f"Clinic: {appointment.doctor.clinic_address}\n\n"
            "This is an appointment confirmation only. This system does not provide diagnosis or treatment."
        ),
    )


def appointment_booked_patient_html(appointment) -> str:
    patient_name = escape(appointment.patient.user.full_name)
    doctor_name = escape(appointment.doctor.user.full_name)
    specialty = escape(appointment.doctor.specialty.name)
    clinic = escape(appointment.doctor.clinic_address)
    appointment_time = escape(_format_time(appointment.slot.start_time))
    symptoms = escape(appointment.symptoms or "Not provided")
    notes = escape(appointment.patient_notes or "Not provided")
    return f"""
    <!doctype html>
    <html>
      <body style="margin:0;background:#f6f8fb;font-family:Arial,sans-serif;color:#172033;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f6f8fb;padding:28px 0;">
          <tr>
            <td align="center">
              <table role="presentation" width="620" cellspacing="0" cellpadding="0" style="max-width:620px;width:94%;background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;">
                <tr>
                  <td style="background:#0f766e;padding:22px 28px;color:#ffffff;">
                    <h1 style="margin:0;font-size:22px;line-height:1.3;">Appointment Confirmed</h1>
                    <p style="margin:6px 0 0;font-size:14px;opacity:.9;">Healthcare Appointments</p>
                  </td>
                </tr>
                <tr>
                  <td style="padding:28px;">
                    <p style="margin:0 0 16px;font-size:16px;">Hello <strong>{patient_name}</strong>,</p>
                    <p style="margin:0 0 20px;font-size:15px;line-height:1.6;">Your appointment has been booked successfully. Please review the details below.</p>
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">
                      <tr><td style="padding:12px 14px;background:#f9fafb;width:34%;font-weight:bold;">Doctor</td><td style="padding:12px 14px;">{doctor_name}</td></tr>
                      <tr><td style="padding:12px 14px;background:#f9fafb;font-weight:bold;">Specialty</td><td style="padding:12px 14px;">{specialty}</td></tr>
                      <tr><td style="padding:12px 14px;background:#f9fafb;font-weight:bold;">Date & Time</td><td style="padding:12px 14px;">{appointment_time}</td></tr>
                      <tr><td style="padding:12px 14px;background:#f9fafb;font-weight:bold;">Clinic</td><td style="padding:12px 14px;">{clinic}</td></tr>
                      <tr><td style="padding:12px 14px;background:#f9fafb;font-weight:bold;">Symptoms</td><td style="padding:12px 14px;">{symptoms}</td></tr>
                      <tr><td style="padding:12px 14px;background:#f9fafb;font-weight:bold;">Notes</td><td style="padding:12px 14px;">{notes}</td></tr>
                    </table>
                    <div style="margin-top:22px;padding:14px 16px;background:#ecfdf5;border:1px solid #bbf7d0;border-radius:8px;color:#065f46;font-size:14px;line-height:1.5;">
                      Please arrive a little early and bring any previous reports or medication list if available.
                    </div>
                    <p style="margin:22px 0 0;font-size:12px;line-height:1.6;color:#667085;">This email confirms your appointment only. This system does not diagnose disease, prescribe medicine, or replace a qualified doctor.</p>
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """


def appointment_booked_doctor(appointment) -> tuple[str, str]:
    appointment_time = _format_time(appointment.slot.start_time)
    return (
        "New appointment booked",
        (
            f"{appointment.patient.user.full_name} booked an appointment for {appointment_time}.\n"
            f"Symptoms/notes: {appointment.symptoms or 'Not provided'}"
        ),
    )


def appointment_cancelled(appointment) -> tuple[str, str]:
    return (
        "Appointment cancelled",
        f"Appointment #{appointment.id} scheduled for {appointment.slot.start_time} has been cancelled.",
    )


def appointment_reminder(appointment) -> tuple[str, str]:
    return (
        "Appointment reminder",
        f"Reminder: appointment #{appointment.id} is scheduled for {appointment.slot.start_time}.",
    )


def emergency_warning(message: str) -> tuple[str, str]:
    return ("Emergency triage warning", message)


def review_case_created(case) -> tuple[str, str]:
    return (
        "Human review case created",
        f"Review case #{case.id} needs attention. Risk level: {case.risk_level.value}. Reason: {case.reason}",
    )


def doctor_notes_added(appointment) -> tuple[str, str]:
    return (
        "Doctor notes updated",
        f"Doctor notes were updated for appointment #{appointment.id}.",
    )
