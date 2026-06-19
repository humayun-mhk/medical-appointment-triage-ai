const commonEmailDomainTypos = {
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
};

export function commonEmailDomainMessage(email) {
  const value = String(email || "").trim().toLowerCase();
  const [local, domain] = value.split("@");
  const suggestion = commonEmailDomainTypos[domain];
  return suggestion ? `Email domain looks misspelled. Did you mean ${local}@${suggestion}?` : null;
}
