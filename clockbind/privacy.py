"""Personal-data scan (GDPR / KVKK data minimisation aid).

Looks for values and column names that suggest personal or identifying data, so the user can
replace them with pseudonymous codes before analysis. It reports column, kind and count only;
it never prints, stores or sends the values. It is an aid, not a guarantee: a clean scan does
not prove a file is anonymous, and a hit is not always personal data.
The same rules are implemented in the web app (webapp/template.html, scanPersonalData).
"""
from __future__ import annotations

import re

import pandas as pd

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE = re.compile(r"^(?:\+|00|0)[\d\s().\-/]{8,}$")
IBAN = re.compile(r"\b[A-Z]{2}\d{2}(?:\s?[A-Z0-9]{4}){2,7}(?:\s?[A-Z0-9]{1,4})?\b")
DIGITS = re.compile(r"\D")
DECIMAL = re.compile(r"-?\d+[.,]\d+")
NUMBERLIKE = re.compile(r"[\d\s\-]+")          # only digits, spaces, dashes (no decimals, no letters)
CODE = re.compile(r"[^\W\d_]+[ _\-]?[A-Z0-9]{1,4}")  # pseudonymous codes such as "Company A", "Firm 3", "EP-D01"

# Column names that usually hold names, contact details or identifiers (EN, TR, HU, IT, FA).
HEADER_WORDS = [
    "name", "first name", "last name", "surname", "full name", "contact", "customer", "client", "company", "firm", "owner",
    "address", "street", "e-mail", "email", "phone", "mobile", "telephone", "birth", "passport", "national id", "tax id", "iban",
    "ad", "adı", "soyad", "soyadı", "isim", "müşteri", "firma", "şirket", "adres", "telefon", "doğum", "tc kimlik", "tckn", "vergi no",
    "név", "vezetéknév", "keresztnév", "ügyfél", "cég", "cím", "születési", "adóazonosító", "taj",
    "nome", "cognome", "cliente", "azienda", "indirizzo", "telefono", "codice fiscale",
    "نام", "نام خانوادگی", "مشتری", "شرکت", "آدرس", "تلفن", "کد ملی",
]


def _iban_ok(s: str) -> bool:
    s = s.replace(" ", "").upper()
    if not 15 <= len(s) <= 34:
        return False
    num = "".join(str(int(c, 36)) for c in s[4:] + s[:4])
    return int(num) % 97 == 1


def _tckn_ok(d: str) -> bool:
    if len(d) != 11 or d[0] == "0" or not d.isdigit():
        return False
    n = [int(c) for c in d]
    return (7 * sum(n[0:9:2]) - sum(n[1:8:2])) % 10 == n[9] and sum(n[:10]) % 10 == n[10]


def _hu_tax_ok(d: str) -> bool:
    if len(d) != 10 or d[0] != "8" or not d.isdigit():
        return False
    n = [int(c) for c in d]
    return sum(n[i] * (i + 1) for i in range(9)) % 11 == n[9]


def _luhn_ok(d: str) -> bool:
    if not 13 <= len(d) <= 19 or not d.isdigit():
        return False
    s, alt = 0, False
    for c in reversed(d):
        x = int(c)
        if alt:
            x = x * 2 - 9 if x > 4 else x * 2
        s += x
        alt = not alt
    return s % 10 == 0


def classify(value) -> list[str]:
    """Kinds of personal data a single cell looks like."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return []
    s = str(value).strip()
    if not s:
        return []
    kinds = []
    if EMAIL.search(s):
        kinds.append("e-mail address")
    d = DIGITS.sub("", s)
    if PHONE.match(s) and 9 <= len(d) <= 15 and not DECIMAL.fullmatch(s):
        kinds.append("phone number")
    m = IBAN.search(s.upper())
    if m and _iban_ok(m.group(0)):
        kinds.append("bank account (IBAN)")
    numeric_id = bool(NUMBERLIKE.fullmatch(s))
    if numeric_id and _tckn_ok(d) and len(s) <= 14:
        kinds.append("Turkish ID number (TCKN)")
    if numeric_id and _hu_tax_ok(d) and len(s) <= 13:
        kinds.append("Hungarian tax ID")
    if numeric_id and _luhn_ok(d) and len(s) <= 23 and "phone number" not in kinds:
        kinds.append("payment card number")
    return kinds


def _norm(x: str) -> str:
    return re.sub(r"[_\-.]+", " ", str(x)).strip().lower()


CODES = {"y", "n", "u", "yes", "no", "unknown", "true", "false", "pass", "fail", "hold", "held", "na", "n/a", "none", "missing", "other",
         "pending", "human pending", "user decision", "not documented", "not reviewed", "complete", "completed", "not applicable"}


def header_hint(col: str) -> bool:
    c = _norm(col)
    words = set(c.split())
    for w in map(_norm, HEADER_WORDS):
        if (" " in w and w in c) or w in words:
            return True
    return False


def _free_text(values) -> int:
    """Cells that look like written names/addresses rather than codes (so coded columns are not flagged)."""
    vals = [str(v).strip() for v in values if v is not None and not (isinstance(v, float) and pd.isna(v)) and str(v).strip()]
    words = [v for v in vals if v.lower() not in CODES and not CODE.fullmatch(v) and sum(ch.isalpha() for ch in v) >= 3]
    return len(words) if len(set(words)) > 3 or any(" " in v for v in words) else 0


def scan_dataframe(df: pd.DataFrame) -> list[dict]:
    """Findings: [{'column', 'kind', 'count'}]. Values are never returned."""
    out = []
    for col in df.columns:
        counts: dict[str, int] = {}
        for v in df[col].tolist():
            for k in classify(v):
                counts[k] = counts.get(k, 0) + 1
        for k, n in counts.items():
            out.append({"column": str(col), "kind": k, "count": n})
        n_text = _free_text(df[col].tolist()) if header_hint(col) else 0
        if n_text:
            out.append({"column": str(col), "kind": "names or identifiers (column name and content)", "count": n_text})
    return out


ADVICE = ("Possible personal or identifying data. Under GDPR (EU 2016/679) and KVKK (Law No. 6698), analyse "
          "pseudonymised codes only: replace names, contacts and ID numbers with codes and keep the key file "
          "separately and securely. ClockBind processes files locally and does not upload them.")
