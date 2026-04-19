# -*- coding: utf-8 -*-
"""Anthropic Claude API wrapper with prompt caching."""
import os
from anthropic import AsyncAnthropic
from prompts import SYSTEM_PROMPT

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 400

_client: AsyncAnthropic | None = None

def _get_client() -> AsyncAnthropic:
    global _client
    if _client is None:
        _client = AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    return _client

async def ask(history: list[dict], user_msg: str) -> tuple[str, bool]:
    """
    Returns (answer_text, offer_consultation).
    offer_consultation=True when the answer signals that a human attorney
    is needed — either the question is outside scope (other visas) or it
    requires individual case review (personal facts, strategy, документы).
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
            }
        ],
        messages=messages,
    )

    text = "".join(b.text for b in resp.content if b.type == "text").strip()

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
