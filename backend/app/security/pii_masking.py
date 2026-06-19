import re


def mask_email(email: str | None) -> str:
    if not email or "@" not in email:
        return email or ""
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "*"
    else:
        masked_local = f"{local[0]}{'*' * (len(local) - 2)}{local[-1]}"
    return f"{masked_local}@{domain}"


def mask_phone(phone: str | None) -> str:
    if not phone:
        return ""
    digits = re.sub(r"\D", "", phone)
    if len(digits) <= 4:
        return "*" * len(digits)
    return f"{'*' * (len(digits) - 4)}{digits[-4:]}"


def mask_address(address: str | None) -> str:
    if not address:
        return ""
    parts = address.split()
    if len(parts) <= 2:
        return "***"
    return f"{parts[0]} {'*' * 8} {parts[-1]}"


def mask_emergency_contact(value: str | None) -> str:
    return mask_phone(value)


def mask_pii_payload(payload):
    if isinstance(payload, list):
        return [mask_pii_payload(item) for item in payload]
    if not isinstance(payload, dict):
        return payload
    masked = {}
    for key, value in payload.items():
        lowered = key.lower()
        if "email" in lowered:
            masked[key] = mask_email(str(value))
        elif "phone" in lowered or "contact" in lowered:
            masked[key] = mask_phone(str(value))
        elif "address" in lowered:
            masked[key] = mask_address(str(value))
        elif isinstance(value, (dict, list)):
            masked[key] = mask_pii_payload(value)
        else:
            masked[key] = value
    return masked
