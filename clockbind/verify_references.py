#!/usr/bin/env python3
"""
verify_references.py — verify academic references against Crossref and OpenAlex.

Purpose
-------
Doctoral work requires every citation to be independently verifiable. This script
takes a list of references and checks each one against public bibliographic APIs.
It reports what the registry actually holds, and flags any field that disagrees
with what you supplied.

It does not invent metadata. If a reference cannot be matched, it says so.

Input formats
-------------
1. CSV with any of these columns (case-insensitive, all optional except one of
   doi / title):
       doi, authors, year, title, journal, volume, issue, pages
2. Plain text, one reference per line, free-form.

Usage
-----
    python verify_references.py refs.csv --mailto you@example.com
    python verify_references.py refs.txt --mailto you@example.com --out report
    python verify_references.py refs.csv --mailto you@example.com --strict

Output
------
    <out>.csv   one row per reference with status and registry metadata
    <out>.md    human-readable report grouped by status

Status values
-------------
    VERIFIED     DOI resolves and supplied fields agree with the registry
    PARTIAL      Record found, but one or more supplied fields disagree
    MATCH_FOUND  No DOI supplied; a strong candidate was found (check it)
    WEAK_MATCH   Candidate found but similarity is low — treat as unverified
    NOT_FOUND    No record located. Do not cite as substantive evidence.
    ERROR        Network or parsing failure; rerun before drawing conclusions
"""

import argparse
import csv
import json
import re
import sys
import time
import unicodedata
from difflib import SequenceMatcher
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

CROSSREF = "https://api.crossref.org/works"
OPENALEX = "https://api.openalex.org/works"
SLEEP = 0.4  # polite pause between calls


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------

def norm(text):
    """Lowercase, strip accents and punctuation, collapse whitespace."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def similar(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def clean_doi(raw):
    if not raw:
        return ""
    d = str(raw).strip()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d, flags=re.I)
    d = re.sub(r"^doi:\s*", "", d, flags=re.I)
    return d.strip().rstrip(".")


def fetch(url, mailto, timeout=25):
    headers = {"User-Agent": f"reference-verifier/1.0 (mailto:{mailto})"}
    req = Request(url, headers=headers)
    with urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", errors="replace"))


def first_surname(authors):
    """Pull a plausible first-author surname out of a free-form author string."""
    if not authors:
        return ""
    chunk = re.split(r"[,;&]| and ", str(authors))[0].strip()
    parts = [p for p in chunk.split() if len(p) > 1 and not p.endswith(".")]
    return parts[-1] if parts else chunk


# ----------------------------------------------------------------------
# registry parsing
# ----------------------------------------------------------------------

def parse_crossref(item):
    title = (item.get("title") or [""])[0]
    container = (item.get("container-title") or [""])[0]
    authors = []
    for a in item.get("author", []) or []:
        fam = a.get("family") or a.get("name") or ""
        if fam:
            authors.append(fam)
    year = ""
    for key in ("published-print", "published-online", "issued", "created"):
        dp = (item.get(key) or {}).get("date-parts") or []
        if dp and dp[0] and dp[0][0]:
            year = str(dp[0][0])
            break
    return {
        "source": "crossref",
        "doi": item.get("DOI", ""),
        "title": title,
        "journal": container,
        "authors": "; ".join(authors),
        "first_author": authors[0] if authors else "",
        "year": year,
        "volume": item.get("volume", ""),
        "issue": item.get("issue", ""),
        "pages": item.get("page", ""),
        "type": item.get("type", ""),
        "url": f"https://doi.org/{item.get('DOI','')}" if item.get("DOI") else "",
    }


def parse_openalex(item):
    authors = []
    for a in item.get("authorships", []) or []:
        name = (a.get("author") or {}).get("display_name", "")
        if name:
            authors.append(name.split()[-1])
    loc = item.get("primary_location") or {}
    src = (loc.get("source") or {}) if isinstance(loc, dict) else {}
    return {
        "source": "openalex",
        "doi": clean_doi(item.get("doi", "")),
        "title": item.get("title") or item.get("display_name") or "",
        "journal": src.get("display_name", ""),
        "authors": "; ".join(authors),
        "first_author": authors[0] if authors else "",
        "year": str(item.get("publication_year") or ""),
        "volume": (item.get("biblio") or {}).get("volume", "") or "",
        "issue": (item.get("biblio") or {}).get("issue", "") or "",
        "pages": "-".join(x for x in [(item.get("biblio") or {}).get("first_page") or "",
                                      (item.get("biblio") or {}).get("last_page") or ""] if x),
        "type": item.get("type", ""),
        "url": item.get("doi", "") or "",
    }


# ----------------------------------------------------------------------
# lookups
# ----------------------------------------------------------------------

def by_doi(doi, mailto):
    try:
        data = fetch(f"{CROSSREF}/{quote(doi)}?mailto={quote(mailto)}", mailto)
        return parse_crossref(data["message"])
    except HTTPError as e:
        if e.code == 404:
            pass
        else:
            return {"error": f"crossref HTTP {e.code}"}
    except (URLError, KeyError, json.JSONDecodeError) as e:
        return {"error": f"crossref {type(e).__name__}"}
    # fall back to OpenAlex
    try:
        data = fetch(f"{OPENALEX}/doi:{quote(doi)}?mailto={quote(mailto)}", mailto)
        return parse_openalex(data)
    except Exception:
        return None


def by_search(ref, mailto, rows=5):
    q = " ".join(str(x) for x in [ref.get("authors", ""), ref.get("title", ""),
                                  ref.get("journal", ""), ref.get("year", "")] if x)
    if not q.strip():
        return []
    url = (f"{CROSSREF}?query.bibliographic={quote(q[:400])}"
           f"&rows={rows}&mailto={quote(mailto)}")
    try:
        data = fetch(url, mailto)
        return [parse_crossref(i) for i in data["message"]["items"]]
    except Exception:
        return []


# ----------------------------------------------------------------------
# comparison
# ----------------------------------------------------------------------

def compare(supplied, found, strict=False):
    """Return (list_of_disagreements, title_similarity)."""
    issues = []
    tsim = 1.0
    if supplied.get("title"):
        tsim = similar(supplied["title"], found.get("title", ""))
        if tsim < 0.80:
            issues.append(f"title differs (similarity {tsim:.2f})")
    if supplied.get("year") and found.get("year"):
        try:
            if abs(int(str(supplied["year"])[:4]) - int(found["year"])) > 1:
                issues.append(f"year: supplied {supplied['year']}, registry {found['year']}")
        except ValueError:
            pass
    if supplied.get("authors") and found.get("first_author"):
        sn = first_surname(supplied["authors"])
        if sn and similar(sn, found["first_author"]) < 0.75:
            issues.append(f"first author: supplied '{sn}', registry '{found['first_author']}'")
    if supplied.get("journal") and found.get("journal"):
        if similar(supplied["journal"], found["journal"]) < 0.62:
            issues.append(f"journal: supplied '{supplied['journal']}', registry '{found['journal']}'")
    if strict:
        for f in ("volume", "issue", "pages"):
            if supplied.get(f) and found.get(f):
                if norm(supplied[f]) != norm(found[f]):
                    issues.append(f"{f}: supplied '{supplied[f]}', registry '{found[f]}'")
    return issues, tsim


def verify_one(ref, mailto, strict=False):
    doi = clean_doi(ref.get("doi", ""))
    if doi:
        found = by_doi(doi, mailto)
        if found is None:
            return {"status": "NOT_FOUND", "found": None,
                    "notes": "DOI does not resolve in Crossref or OpenAlex"}
        if "error" in found:
            return {"status": "ERROR", "found": None, "notes": found["error"]}
        issues, _ = compare(ref, found, strict)
        return {"status": "VERIFIED" if not issues else "PARTIAL",
                "found": found, "notes": "; ".join(issues)}

    candidates = by_search(ref, mailto)
    if not candidates:
        return {"status": "NOT_FOUND", "found": None,
                "notes": "no DOI supplied and no candidate located"}
    best, best_score = None, -1.0
    for c in candidates:
        score = similar(ref.get("title", ""), c.get("title", ""))
        if ref.get("year") and c.get("year") and str(ref["year"])[:4] == c["year"]:
            score += 0.10
        if score > best_score:
            best, best_score = c, score
    issues, tsim = compare(ref, best, strict)
    if tsim >= 0.85 and not [i for i in issues if i.startswith("title")]:
        status = "MATCH_FOUND"
    else:
        status = "WEAK_MATCH"
    return {"status": status, "found": best,
            "notes": "; ".join(issues) or f"candidate DOI {best.get('doi','')}"}


# ----------------------------------------------------------------------
# input
# ----------------------------------------------------------------------

def load(path):
    refs = []
    if path.lower().endswith(".csv"):
        with open(path, newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                refs.append({(k or "").strip().lower(): (v or "").strip()
                             for k, v in row.items()})
    else:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                m = re.search(r"(10\.\d{4,9}/[^\s,;]+)", line)
                y = re.search(r"\b(19|20)\d{2}\b", line)
                refs.append({
                    "raw": line,
                    "doi": m.group(1).rstrip(".") if m else "",
                    "title": line,
                    "year": y.group(0) if y else "",
                })
    return refs


# ----------------------------------------------------------------------
# output
# ----------------------------------------------------------------------

ORDER = ["NOT_FOUND", "WEAK_MATCH", "PARTIAL", "MATCH_FOUND", "VERIFIED", "ERROR"]

ADVICE = {
    "VERIFIED": "Safe to cite. Registry agrees with what you supplied.",
    "PARTIAL": "Record exists but a field disagrees. Correct your entry before citing.",
    "MATCH_FOUND": "No DOI was supplied. Check the candidate below, then add its DOI.",
    "WEAK_MATCH": "Similarity is low. Treat as UNVERIFIED until checked by hand.",
    "NOT_FOUND": "Do not cite as substantive evidence until located manually.",
    "ERROR": "Lookup failed. Rerun before concluding anything about this entry.",
}


def write_reports(results, out):
    fields = ["n", "status", "notes", "supplied_title", "supplied_year", "supplied_doi",
              "registry_doi", "registry_title", "registry_authors", "registry_year",
              "registry_journal", "registry_volume", "registry_issue", "registry_pages",
              "registry_source", "url"]
    with open(out + ".csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        for i, (ref, res) in enumerate(results, 1):
            f = res.get("found") or {}
            w.writerow({
                "n": i, "status": res["status"], "notes": res.get("notes", ""),
                "supplied_title": ref.get("title", "")[:300],
                "supplied_year": ref.get("year", ""),
                "supplied_doi": clean_doi(ref.get("doi", "")),
                "registry_doi": f.get("doi", ""), "registry_title": f.get("title", ""),
                "registry_authors": f.get("authors", ""), "registry_year": f.get("year", ""),
                "registry_journal": f.get("journal", ""), "registry_volume": f.get("volume", ""),
                "registry_issue": f.get("issue", ""), "registry_pages": f.get("pages", ""),
                "registry_source": f.get("source", ""), "url": f.get("url", ""),
            })

    counts = {}
    for _, r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    lines = ["# Reference verification report", ""]
    lines.append(f"Checked {len(results)} references against Crossref and OpenAlex.")
    lines.append("")
    lines.append("| Status | Count | What to do |")
    lines.append("|---|---|---|")
    for s in ORDER:
        if s in counts:
            lines.append(f"| {s} | {counts[s]} | {ADVICE[s]} |")
    lines.append("")
    for s in ORDER:
        group = [(i, ref, res) for i, (ref, res) in enumerate(results, 1)
                 if res["status"] == s]
        if not group:
            continue
        lines.append(f"## {s} ({len(group)})")
        lines.append("")
        for i, ref, res in group:
            f = res.get("found") or {}
            supplied = ref.get("raw") or ref.get("title", "")
            lines.append(f"**{i}.** {supplied[:240]}")
            if res.get("notes"):
                lines.append(f"- Note: {res['notes']}")
            if f:
                cite = f"{f.get('authors','')} ({f.get('year','')}). {f.get('title','')}. "
                cite += f"*{f.get('journal','')}*"
                if f.get("volume"):
                    cite += f", {f['volume']}"
                if f.get("issue"):
                    cite += f"({f['issue']})"
                if f.get("pages"):
                    cite += f", {f['pages']}"
                cite += "."
                lines.append(f"- Registry: {cite}")
                if f.get("doi"):
                    lines.append(f"- DOI: {f['doi']}")
            lines.append("")
    with open(out + ".md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))
    return counts


def main():
    ap = argparse.ArgumentParser(description="Verify academic references against Crossref/OpenAlex.")
    ap.add_argument("input", help="CSV or plain-text file of references")
    ap.add_argument("--mailto", required=True, help="Your email (required by the polite API pool)")
    ap.add_argument("--out", default="verification_report", help="Output basename")
    ap.add_argument("--strict", action="store_true", help="Also compare volume, issue, pages")
    args = ap.parse_args()

    refs = load(args.input)
    if not refs:
        sys.exit("No references found in input.")

    results = []
    for i, ref in enumerate(refs, 1):
        label = (ref.get("title") or ref.get("doi") or "")[:60]
        print(f"[{i}/{len(refs)}] {label}...", flush=True)
        try:
            res = verify_one(ref, args.mailto, args.strict)
        except Exception as e:
            res = {"status": "ERROR", "found": None, "notes": f"{type(e).__name__}: {e}"}
        results.append((ref, res))
        time.sleep(SLEEP)

    counts = write_reports(results, args.out)
    print("\nSummary")
    for s in ORDER:
        if s in counts:
            print(f"  {s:<12} {counts[s]}")
    print(f"\nWrote {args.out}.csv and {args.out}.md")
    unsafe = sum(counts.get(s, 0) for s in ("NOT_FOUND", "WEAK_MATCH", "ERROR"))
    if unsafe:
        print(f"WARNING: {unsafe} reference(s) are not safe to cite as substantive evidence.")


if __name__ == "__main__":
    main()
