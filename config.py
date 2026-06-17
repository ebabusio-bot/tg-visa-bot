# -*- coding: utf-8 -*-
"""White-label configuration read from the environment.

Everything here lets the SAME codebase be resold to different firms by editing
only `.env` — no code fork. Two kinds of values live here:

  • Firm branding (FIRM_NAME) and firm SERVICE prices (consultation, legal
    service, per-member I-485). These differ per firm, so they are env-driven.

  • Government USCIS fees (I-140, I-485, Premium Processing, asylum program fee)
    are NOT here: they are facts, identical for every firm, so they stay written
    out literally in the texts (see i18n.py / prompts.py).
"""
import os


def _str(env_key: str, default: str) -> str:
    return (os.environ.get(env_key, "") or "").strip() or default


# Firm/brand name. Empty → no branding line (generic bot, current behaviour).
FIRM_NAME = _str("FIRM_NAME", "")

# Firm SERVICE prices, as DISPLAY strings WITHOUT the leading "$" (templates add
# the "$"). Defaults reproduce the original hardcoded prices, so an unconfigured
# deploy behaves exactly as before.
PRICE_CONSULT = _str("PRICE_CONSULT", "300")          # initial consultation
PRICE_PETITION = _str("PRICE_PETITION", "15 000")     # EB-1 / EB-2 NIW legal service
PRICE_I485_MEMBER = _str("PRICE_I485_MEMBER", "500")  # I-485, per family member


def prices() -> dict:
    """Substitution map for the {consult}/{petition}/{member} placeholders used
    in the pricing texts."""
    return {
        "consult": PRICE_CONSULT,
        "petition": PRICE_PETITION,
        "member": PRICE_I485_MEMBER,
    }
