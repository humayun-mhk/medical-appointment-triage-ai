from app.core.config import settings


def send_sms(recipient: str, message: str) -> dict:
    if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_PHONE_NUMBER:
        try:
            from twilio.rest import Client

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(body=message, from_=settings.TWILIO_PHONE_NUMBER, to=recipient)
            return {"status": "sent", "provider": "twilio", "error": None}
        except Exception as exc:
            return {"status": "failed", "provider": "twilio", "error": str(exc)}

    print(f"[sms fallback] To={recipient} Message={message}")
    return {"status": "sent", "provider": "console", "error": None}
