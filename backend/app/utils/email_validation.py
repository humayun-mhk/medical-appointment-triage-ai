COMMON_EMAIL_DOMAIN_TYPOS = {
    "gmil.com": "gmail.com",
    "gmai.com": "gmail.com",
    "gmail.co": "gmail.com",
    "gnail.com": "gmail.com",
    "hotmial.com": "hotmail.com",
    "hotmai.com": "hotmail.com",
    "outlok.com": "outlook.com",
    "outloo.com": "outlook.com",
    "yaho.com": "yahoo.com",
    "yhoo.com": "yahoo.com",
}


def validate_common_email_domain(email: str) -> str:
    value = str(email).strip().lower()
    domain = value.rsplit("@", 1)[-1]
    suggestion = COMMON_EMAIL_DOMAIN_TYPOS.get(domain)
    if suggestion:
        raise ValueError(f"Email domain looks misspelled. Did you mean {value.rsplit('@', 1)[0]}@{suggestion}?")
    return value
