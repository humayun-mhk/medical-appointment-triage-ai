import json
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.core.config import settings


def _sender_email() -> str:
    return settings.SMTP_FROM_EMAIL or settings.SMTP_USER or "noreply@example.com"


def _sender() -> str:
    return formataddr((settings.SMTP_FROM_NAME, _sender_email()))


def _send_brevo_email(recipient: str, subject: str, message: str, html_message: str | None = None) -> dict:
    payload = {
        "sender": {"name": settings.SMTP_FROM_NAME, "email": _sender_email()},
        "to": [{"email": recipient}],
        "subject": subject,
        "textContent": message,
    }
    if html_message:
        payload["htmlContent"] = html_message

    request = Request(
        settings.BREVO_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "accept": "application/json",
            "api-key": settings.BREVO_API_KEY or "",
            "content-type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=settings.SMTP_TIMEOUT_SECONDS) as response:
            if 200 <= response.status < 300:
                return {"status": "sent", "provider": "brevo", "error": None}
            body = response.read().decode("utf-8", errors="replace")
            return {
                "status": "failed",
                "provider": "brevo",
                "error": f"Brevo API returned {response.status}: {body}",
            }
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {"status": "failed", "provider": "brevo", "error": f"{exc.code}: {body}"}
    except URLError as exc:
        return {"status": "failed", "provider": "brevo", "error": str(exc.reason)}
    except Exception as exc:
        return {"status": "failed", "provider": "brevo", "error": str(exc)}


def send_email(recipient: str, subject: str, message: str, html_message: str | None = None) -> dict:
    if settings.EMAIL_PROVIDER == "brevo" and settings.BREVO_API_KEY:
        return _send_brevo_email(recipient, subject or "Healthcare notification", message, html_message)

    if settings.EMAIL_PROVIDER == "sendgrid" and settings.SENDGRID_API_KEY:
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            mail = Mail(
                from_email=_sender_email(),
                to_emails=recipient,
                subject=subject,
                plain_text_content=message,
                html_content=html_message,
            )
            SendGridAPIClient(settings.SENDGRID_API_KEY).send(mail)
            return {"status": "sent", "provider": "sendgrid", "error": None}
        except Exception as exc:
            return {"status": "failed", "provider": "sendgrid", "error": str(exc)}

    if settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD:
        try:
            email = EmailMessage()
            email["From"] = _sender()
            email["To"] = recipient
            email["Subject"] = subject
            email.set_content(message)
            if html_message:
                email.add_alternative(html_message, subtype="html")
            with smtplib.SMTP(
                settings.SMTP_HOST,
                settings.SMTP_PORT,
                timeout=settings.SMTP_TIMEOUT_SECONDS,
            ) as smtp:
                if settings.SMTP_USE_TLS:
                    smtp.starttls()
                smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                refused = smtp.send_message(email)
                if refused:
                    return {
                        "status": "failed",
                        "provider": "smtp",
                        "error": f"SMTP refused recipients: {refused}",
                    }
            return {"status": "sent", "provider": "smtp", "error": None}
        except Exception as exc:
            return {"status": "failed", "provider": "smtp", "error": str(exc)}

    print(f"[email fallback] To={recipient} Subject={subject} Message={message}")
    return {"status": "sent", "provider": "console", "error": None}
