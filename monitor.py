# -*- coding: utf-8 -*-
"""Daily monitoring of official USCIS / US State Department pages.

For each watched page we fetch the HTML, reduce it to normalized visible text,
and compare against the last stored snapshot. When the text changes we ask the
LLM whether the change is *substantive* for applicants (document requirements,
criteria, timelines, fees, procedure) — cosmetic churn (nav, layout, page-update
dates) is filtered out so the admin only hears about real changes.

Snapshots live in the `monitor_snapshots` table (see db.py). The daily job and
the /checkupdates admin command both call check_all().
"""
import difflib
import hashlib
import html as _html
import logging
import re

import httpx

import db
import llm

log = logging.getLogger("monitor")

# Watched official sources — stable, server-rendered pages. Keep this list
# aligned with the visa categories the bot supports.
SOURCES = [
    {"key": "uscis_eb1", "category": "EB-1",
     "name": "USCIS — EB-1 (Extraordinary Ability и др.)",
     "url": "https://www.uscis.gov/working-in-the-united-states/permanent-workers/employment-based-immigration-first-preference-eb-1"},
    {"key": "uscis_eb2", "category": "EB-2 / NIW",
     "name": "USCIS — EB-2 (включая NIW)",
     "url": "https://www.uscis.gov/working-in-the-united-states/permanent-workers/employment-based-immigration-second-preference-eb-2"},
    {"key": "uscis_eb3", "category": "EB-3",
     "name": "USCIS — EB-3 (Skilled / Professional / Other)",
     "url": "https://www.uscis.gov/working-in-the-united-states/permanent-workers/employment-based-immigration-third-preference-eb-3"},
    {"key": "uscis_o1", "category": "O-1",
     "name": "USCIS — O-1 (Extraordinary Ability)",
     "url": "https://www.uscis.gov/working-in-the-united-states/temporary-workers/o-1-individuals-with-extraordinary-ability-or-achievement"},
    {"key": "uscis_e2", "category": "E-2",
     "name": "USCIS — E-2 Treaty Investors",
     "url": "https://www.uscis.gov/working-in-the-united-states/temporary-workers/e-2-treaty-investors"},
    {"key": "uscis_asylum", "category": "Asylum",
     "name": "USCIS — Asylum (убежище)",
     "url": "https://www.uscis.gov/humanitarian/refugees-and-asylum/asylum"},
    {"key": "uscis_premium", "category": "Premium Processing",
     "name": "USCIS — Premium Processing (I-907)",
     "url": "https://www.uscis.gov/forms/all-forms/how-do-i-request-premium-processing"},
    {"key": "dos_visa_bulletin", "category": "Visa Bulletin",
     "name": "Госдеп США — Visa Bulletin",
     "url": "https://travel.state.gov/content/travel/en/legal/visa-law0/visa-bulletin.html"},
]

_UA = "Mozilla/5.0 (compatible; SunnyFlBot/1.0; +https://t.me/SunnyFl_bot)"

_DROP_BLOCKS = re.compile(r"(?is)<(script|style|noscript|svg|head)[^>]*>.*?</\1>")
_TAGS = re.compile(r"(?s)<[^>]+>")
_INLINE_WS = re.compile(r"[ \t\r\f\v]+")


def _normalize(raw: str) -> str:
    """Reduce HTML to normalized visible text for stable diffing."""
    t = _DROP_BLOCKS.sub(" ", raw)
    t = _TAGS.sub("\n", t)
    t = _html.unescape(t)
    lines = []
    for ln in t.splitlines():
        ln = _INLINE_WS.sub(" ", ln).strip()
        if len(ln) > 2:           # drop empty / single-char nav noise
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
    """Unified diff reduced to just the changed (+/-) lines, capped in size."""
    raw = difflib.unified_diff(
        old.splitlines(), new.splitlines(), lineterm="", n=0
    )
    changed = [
        ln for ln in raw
        if ln and ln[0] in "+-" and not ln.startswith(("+++", "---"))
    ]
    return "\n".join(changed)[:max_chars]


def _meta(src: dict) -> dict:
    return {"key": src["key"], "name": src["name"],
            "url": src["url"], "category": src["category"]}


async def check_source(src: dict) -> dict:
    """Fetch one source and classify the result.

    status is one of: 'new' (baseline stored), 'unchanged', 'cosmetic'
    (text changed but no applicant impact), 'changed' (substantive — `summary`
    is set), or 'error' (fetch/parse failed)."""
    raw = await _fetch(src["url"])
    if raw is None:
        return {**_meta(src), "status": "error", "summary": None}
    text = _normalize(raw)
    if len(text) < 200:
        # Block page or JS shell — don't overwrite a good baseline with junk.
        log.warning("monitor %s: suspiciously short text (%d chars)",
                    src["key"], len(text))
        return {**_meta(src), "status": "error", "summary": None}

    h = hashlib.sha256(text.encode("utf-8")).hexdigest()
    prev = db.get_monitor_snapshot(src["key"])

    if prev is None:
        db.save_monitor_snapshot(src["key"], src["url"], h, text, changed=False)
        return {**_meta(src), "status": "new", "summary": None}

    if prev["content_hash"] == h:
        db.save_monitor_snapshot(src["key"], src["url"], h, text, changed=False)
        return {**_meta(src), "status": "unchanged", "summary": None}

    # Text changed — let the LLM decide whether it matters to applicants.
    diff_text = _diff(prev["content_text"] or "", text)
    summary = None
    if diff_text.strip():
        try:
            summary = await llm.summarize_change(
                src["name"], src["category"], diff_text)
        except Exception as e:
            log.warning("monitor summarize failed for %s: %s", src["key"], e)
    substantive = summary is not None
    db.save_monitor_snapshot(src["key"], src["url"], h, text, changed=substantive)
    return {
        **_meta(src),
        "status": "changed" if substantive else "cosmetic",
        "summary": summary,
    }


async def check_all() -> list[dict]:
    """Check every source sequentially (gentle on the servers). Returns the
    per-source result dicts."""
    results = []
    for src in SOURCES:
        results.append(await check_source(src))
    return results
