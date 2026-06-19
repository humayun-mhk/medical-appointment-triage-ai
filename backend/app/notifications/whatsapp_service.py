from app.core.config import settings


def send_whatsapp(recipient: str, message: str) -> dict:
    if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN and settings.TWILIO_WHATSAPP_NUMBER:
        try:
            from twilio.rest import Client

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                body=message,
                from_=f"whatsapp:{settings.TWILIO_WHATSAPP_NUMBER}",
                to=f"whatsapp:{recipient}",
            )
            return {"status": "sent", "provider": "twilio_whatsapp", "error": None}
        except Exception as exc:
            return {"status": "failed", "provider": "twilio_whatsapp", "error": str(exc)}

    print(f"[whatsapp fallback] To={recipient} Message={message}")
    return {"status": "sent", "provider": "console", "error": None}
