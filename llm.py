# -*- coding: utf-8 -*-
"""Anthropic Claude API wrapper with prompt caching."""
import logging
import os
import re
from anthropic import AsyncAnthropic
from prompts import SYSTEM_PROMPT
from i18n import LANG_NATIVE

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1500

log = logging.getLogger("llm")

_client: AsyncAnthropic | None = None

def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip())
    return _client


# Appended as a second (uncached) system block so the main SYSTEM_PROMPT
# cache is preserved. The model sees both.
def _lang_directive(lang: str) -> str:
    if lang == "ru":
        # Russian is the base language of SYSTEM_PROMPT — no override needed.
        return (
            "ЯЗЫК ВЫВОДА: отвечай на русском языке.\n"
            "Если в конце ответа пользователь должен быть направлен к специалисту "
            "(вопрос вне специализации, нужна оценка личного дела), добавь литеральный "
            "маркер <<CONSULT>> в самом конце ответа. Маркер — служебный, НЕ переводи и НЕ изменяй его."
        )
    native = LANG_NATIVE.get(lang, "English")
    return (
        f"OUTPUT LANGUAGE: respond ENTIRELY in {native} (lang code: {lang}).\n"
        "• The knowledge base is in Russian — translate every answer to the user's language.\n"
        "• Preserve ALL numeric facts exactly (fees, dates, processing times, dollar amounts, percentages). "
        "Never change a number when translating.\n"
        "• Keep the following tokens in their original English form, do NOT translate or transliterate: "
        "visa category codes (EB-1A, EB-1B, EB-1C, EB-2, EB-2 NIW, EB-3, EB-5, O-1, O-1A, O-1B, E-2, "
        "L-1, H-1B, F-1, K-1, B-1, B-2, I-140, I-485, I-765, I-589, I-129, I-131, I-693, I-730, I-907, "
        "I-907, EAD, AP, AOS, PERM, USCIS, AAO, EOIR, NVC, IRS, CBP, DHS, DOS); case names "
        "(Matter of Dhanasar, Kazarian, Cardoza-Fonseca); statutory references if they appear "
        "(INA §, 8 CFR §, 8 U.S.C. §); procedural terms that are terms of art and not translated by "
        "USCIS itself (Premium Processing, Advance Parole, Adjustment of Status, Credible Fear, "
        "Withholding of Removal, National Interest Waiver, Extraordinary Ability, Final Merits, "
        "at-risk, develop and direct, labor certification).\n"
        "• If the user should be directed to a human specialist (question outside scope or needs "
        "individual case review), append the literal marker <<CONSULT>> at the very end of the answer. "
        "The marker is a service token — do NOT translate or alter it.\n"
        "• Do not mention that you translated, do not apologise for the language, do not mix in "
        "Russian phrases."
    )


CONSULT_MARKER = "<<CONSULT>>"
_CONSULT_RE = re.compile(r"\s*<<\s*CONSULT\s*>>\s*$", re.IGNORECASE)


async def ask(history: list[dict], user_msg: str, lang: str = "ru") -> tuple[str, bool]:
    """
    Returns (answer_text, offer_consultation).
    offer_consultation is True when the model emitted the <<CONSULT>> marker,
    which it does in every language when a human attorney is needed.
    """
    messages = list(history) + [{"role": "user", "content": user_msg}]

    resp = await _get_client().messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            },
            {
                "type": "text",
                "text": _lang_directive(lang),
            },
        ],
        messages=messages,
    )

    text = "".join(b.text for b in resp.content if b.type == "text").strip()

    if getattr(resp, "stop_reason", None) == "max_tokens":
        log.warning(
            "LLM hit max_tokens=%d (user_msg=%r, out_chars=%d)",
            MAX_TOKENS, user_msg[:100], len(text),
        )

    # Extract consult marker from anywhere in the text (the model may emit it
    # in the middle of a paragraph if it decides the advice applies mid-answer).
    offer_consultation = CONSULT_MARKER.lower() in text.lower()
    if offer_consultation:
        # Remove the marker (case-insensitive, trim trailing whitespace).
        text = re.sub(r"<<\s*CONSULT\s*>>", "", text, flags=re.IGNORECASE).strip()

    # Russian-keyword fallback (belt-and-braces for pre-marker models or Russian output).
    if not offer_consultation and lang == "ru":
        lowered = text.lower()
        offer_consultation = any(s in lowered for s in [
            "записаться на консультацию",
            "консультацию со специалистом",
            "консультация со специалистом",
            "требует индивидуальной оценки",
            "индивидуальной консультации",
            "индивидуальная оценка",
            "моя специализация ограничена",
            "специализация ограничена",
            "обратитесь к специалисту",
            "обратиться к специалисту",
        ])

    return text, offer_consultation


async def translate(text_ru: str, lang: str) -> str:
    """One-shot translator for fixed strings (e.g. quiz verdicts).
    Preserves numbers, markdown, and US-immigration terms. Called when the
    user is not Russian-speaking and we need to show a Russian-authored
    verdict in their language."""
    if lang == "ru":
        return text_ru
    native = LANG_NATIVE.get(lang, "English")
    resp = await _get_client().messages.create(
        model=MODEL,
        max_tokens=1500,
        system=[{
            "type": "text",
            "text": (
                f"You are a precise translator. Translate the USER message from Russian "
                f"into {native} (language code: {lang}).\n"
                "Rules:\n"
                "• Preserve all numeric values, dates, fees, percentages EXACTLY.\n"
                "• Preserve Markdown formatting (asterisks, underscores, newlines) as-is.\n"
                "• Keep the following in original English form: EB-1A, EB-1B, EB-1C, EB-2, "
                "EB-2 NIW, EB-3, EB-5, O-1, O-1A, O-1B, E-2, L-1, H-1B, I-140, I-485, I-765, "
                "I-589, I-907, USCIS, PERM, Matter of Dhanasar, Kazarian, Premium Processing, "
                "Advance Parole, Adjustment of Status, National Interest Waiver, at-risk, "
                "develop and direct, Final Merits.\n"
                "• Output ONLY the translation, no preamble, no quotes, no explanation."
            ),
        }],
        messages=[{"role": "user", "content": text_ru}],
    )
    out = "".join(b.text for b in resp.content if b.type == "text").strip()
    return out or text_ru
