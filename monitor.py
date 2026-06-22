# -*- coding: utf-8 -*-
"""Daily monitoring of official US immigration sources.

Two channels, because the sources behave differently:

1. Federal Register API (federalregister.gov) — the US government's official
   journal where USCIS / DHS / State publish every rule, fee change, form
   revision and policy notice. This is the authoritative source for "changing
   requirements / approaches / timelines / fees". We track seen document
   numbers and alert on new ones relevant to the bot's visa categories.
   (USCIS's own website is behind Akamai bot protection and returns 403 to
   servers, so we rely on the Federal Register instead — it carries the actual
   rule changes anyway.)

2. State Dept Visa Bulletin (travel.state.gov) — a normal page we can fetch.
   We snapshot its visible text and diff it; the LLM reports substantive
   movement in priority dates.

Both feed check_all(), used by the daily job and the /checkupdates command.
"""
import datetime as _dt
import difflib
import hashlib
import html as _html
import logging
import re

import httpx

import db
import llm

log = logging.getLogger("monitor")

_UA = "Mozilla/5.0 (compatible; SunnyFlBot/1.0; +https://t.me/SunnyFl_bot)"

# ─────────────────────────────────────────────── Federal Register channel

_FEDREG_URL = "https://www.federalregister.gov/api/v1/documents.json"

# Agencies whose immigration rules matter to this bot.
_FEDREG_AGENCIES = [
    ("u-s-citizenship-and-immigration-services", "USCIS"),
    ("homeland-security-department", "DHS"),
    ("state-department", "Госдеп"),
]

# A doc is relevant if its title or abstract mentions any of these (lowercased).
_FEDREG_KEYWORDS = (
    "eb-1", "eb1", "eb-2", "eb2", "eb-3", "eb3", "o-1", "e-2", "treaty investor",
    "asylum", "employment-based", "employment based", "immigrant visa",
    "premium processing", "i-140", "i-485", "i-129", "i-907", "i-589",
    "labor certification", "priority date", "national interest",
    "extraordinary ability", "visa bulletin", "adjustment of status",
    "filing fee", "fee schedule", "fee rule", "form i-", "perm",
)

_FEDREG_LOOKBACK_DAYS = 45


def _today() -> _dt.date:
    return _dt.datetime.now(_dt.timezone.utc).date()


def _relevant(doc: dict) -> bool:
    blob = ((doc.get("title") or "") + " " + (doc.get("abstract") or "")).lower()
    return any(k in blob for k in _FEDREG_KEYWORDS)


async def _fedreg_fetch(agency_slug: str) -> list[dict]:
    since = (_today() - _dt.timedelta(days=_FEDREG_LOOKBACK_DAYS)).isoformat()
    params = {
        "conditions[agencies][]": agency_slug,
        "conditions[publication_date][gte]": since,
        "order": "newest",
        "per_page": 50,
        "fields[]": ["document_number", "title", "abstract", "type",
                     "html_url", "publication_date"],
    }
    async with httpx.AsyncClient(timeout=30, headers={"User-Agent": _UA}) as c:
        r = await c.get(_FEDREG_URL, params=params)
    if r.status_code != 200:
        log.warning("fedreg %s -> HTTP %s", agency_slug, r.status_code)
        return []
    return r.json().get("results", []) or []


async def check_federal_register() -> dict:
    """Return {'status', 'new': [docs]}. On the very first run we silently
    establish a baseline (mark everything seen, alert on nothing).

    Important: new (non-baseline) docs are NOT marked seen here. Each alert
    dict carries its 'doc_id', and the caller marks it seen only AFTER the
    alert is pushed (see job_check_official_updates). That way a crash or
    delivery failure can't permanently suppress a rule-change alert — at worst
    it re-alerts next run."""
    baseline = db.monitor_seen_count() == 0
    new_docs: list[dict] = []
    seen_this_run: set[str] = set()
    any_fetch = False
    for slug, short in _FEDREG_AGENCIES:
        try:
            docs = await _fedreg_fetch(slug)
            any_fetch = True
        except Exception as e:
            log.warning("fedreg fetch %s failed: %s", slug, e)
            continue
        for doc in docs:
            if not _relevant(doc):
                continue
            did = doc.get("document_number")
            if not did or db.has_doc_seen(did) or did in seen_this_run:
                continue
            seen_this_run.add(did)
            if baseline:
                db.mark_doc_seen(did)  # silent baseline, no alert to deliver
            else:
                doc["_agency"] = short
                new_docs.append(doc)

    if not any_fetch:
        return {"status": "error", "new": []}

    # Summarize each new doc in Russian (rare event → cheap).
    out = []
    for doc in new_docs:
        summary = None
        try:
            summary = await llm.summarize_rule(
                doc.get("title", ""), doc.get("abstract", "") or "")
        except Exception as e:
            log.warning("fedreg summarize failed: %s", e)
        out.append({
            "doc_id": doc.get("document_number"),
            "name": f"Federal Register · {doc.get('_agency','')} · {doc.get('type','')}",
            "title": doc.get("title", ""),
            "date": doc.get("publication_date", ""),
            "summary": summary or (doc.get("abstract") or doc.get("title") or ""),
            "url": doc.get("html_url", ""),
        })
    status = "baseline" if baseline else ("new" if out else "unchanged")
    return {"status": status, "new": out}


# ─────────────────────────────────────────────── HTML-scrape channel (Visa Bulletin)

HTML_SOURCES = [
    {"key": "dos_visa_bulletin", "category": "Visa Bulletin",
     "name": "Госдеп США — Visa Bulletin",
     "url": "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html"},
]

_DROP_BLOCKS = re.compile(r"(?is)<(script|style|noscript|svg|head)[^>]*>.*?</\1>")
_TAGS = re.compile(r"(?s)<[^>]+>")
_INLINE_WS = re.compile(r"[ \t\r\f\v]+")


def _normalize(raw: str) -> str:
    t = _DROP_BLOCKS.sub(" ", raw)
    t = _TAGS.sub("\n", t)
    t = _html.unescape(t)
    lines = []
    for ln in t.splitlines():
        ln = _INLINE_WS.sub(" ", ln).strip()
        if len(ln) > 2:
            lines.append(ln)
    return "\n".join(lines).strip()


async def _fetch(url: str) -> str | None:
    try:
        async with httpx.AsyncClient(
            timeout=30, follow_redirects=True, headers={"User-Agent": _UA}
        ) as client:
            r = await client.get(url)
        if r.status_code != 200:
            log.warning("monitor fetch %s -> HTTP %s", url, r.status_code)
            return None
        return r.text
    except Exception as e:
        log.warning("monitor fetch %s failed: %s", url, e)
        return None


def _diff(old: str, new: str, max_chars: int = 6000) -> str:
    raw = difflib.unified_diff(old.splitlines(), new.splitlines(), lineterm="", n=0)
    changed = [ln for ln in raw
               if ln and ln[0] in "+-" and not ln.startswith(("+++", "---"))]
    return "\n".join(changed)[:max_chars]


async def check_html_source(src: dict) -> dict:
    """status: 'new' | 'unchanged' | 'cosmetic' | 'changed' | 'error'."""
    raw = await _fetch(src["url"])
    if raw is None:
        return {"status": "error", "summary": None}
    text = _normalize(raw)
    if len(text) < 200:
        return {"status": "error", "summary": None}
    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    prev = db.get_monitor_snapshot(src["key"])
    if prev is None:
        db.save_monitor_snapshot(src["key"], src["url"], h, text, changed=False)
        return {"status": "new", "summary": None}
    if prev["content_hash"] == h:
        db.save_monitor_snapshot(src["key"], src["url"], h, text, changed=False)
        return {"status": "unchanged", "summary": None}
    diff_text = _diff(prev["content_text"] or "", text)
    summary = None
    if diff_text.strip():
        try:
            summary = await llm.summarize_change(src["name"], src["category"], diff_text)
        except Exception as e:
            log.warning("monitor summarize failed for %s: %s", src["key"], e)
    substantive = summary is not None
    db.save_monitor_snapshot(src["key"], src["url"], h, text, changed=substantive)
    return {"status": "changed" if substantive else "cosmetic", "summary": summary}


# ─────────────────────────────────────────────────────────────── orchestrator

async def check_all() -> dict:
    """Run both channels. Returns:
      {'alerts': [{name, summary, url}], 'report': [{name, status}],
       'fedreg_pending_seen': [doc_id, ...]}.
    `alerts` is what gets pushed to admins; `report` is the status table;
    `fedreg_pending_seen` are Federal Register doc ids the caller must mark seen
    AFTER successfully pushing the alerts (so a failed push re-alerts next run)."""
    alerts: list[dict] = []
    report: list[dict] = []

    for src in HTML_SOURCES:
        r = await check_html_source(src)
        report.append({"name": src["name"], "status": r["status"]})
        if r["status"] == "changed" and r["summary"]:
            alerts.append({"name": src["name"], "summary": r["summary"], "url": src["url"]})

    fr = await check_federal_register()
    report.append({"name": "Federal Register (USCIS / DHS / Госдеп)", "status": fr["status"]})
    pending_seen: list[str] = []
    for d in fr["new"]:
        summary = d["summary"]
        if d.get("title"):
            summary = f"{d['title']}\n\n{summary}"
        alerts.append({"name": d["name"], "summary": summary, "url": d["url"]})
        if d.get("doc_id"):
            pending_seen.append(d["doc_id"])

    return {"alerts": alerts, "report": report, "fedreg_pending_seen": pending_seen}
