# -*- coding: utf-8 -*-
"""WhatsApp notifications via CallMeBot (free).

Used to duplicate "client wants to talk / book" alerts to a second admin who
does not always watch Telegram. Fully optional: if the env vars are not set,
notify() is a silent no-op and the bot behaves exactly as before.

One-time setup for the recipient (the second admin), on their own phone:
  1. Add the CallMeBot number +34 644 84 71 89 to contacts.
  2. Send it the message:  I allow callmebot to send me messages
  3. CallMeBot replies with a personal apikey.
Then set in .env:
  WHATSAPP_NOTIFY_PHONE=<recipient phone, intl format, e.g. +13055551234>
  CALLMEBOT_APIKEY=<the apikey from step 3>
"""
import os
import logging

import httpx

log = logging.getLogger(__name__)

WHATSAPP_PHONE = os.environ.get("WHATSAPP_NOTIFY_PHONE", "").strip()
CALLMEBOT_APIKEY = os.environ.get("CALLMEBOT_APIKEY", "").strip()

_API = "https://api.callmebot.com/whatsapp.php"


def is_configured() -> bool:
    """True only when both the recipient phone and the API key are set."""
    return bool(WHATSAPP_PHONE and CALLMEBOT_APIKEY)


async def notify(text: str) -> bool:
    """Send a plain-text WhatsApp message to the configured recipient.

    Returns True on success, False on no-op (not configured) or any failure.
    Never raises — WhatsApp delivery must not break the Telegram flow.
    """
    if not is_configured():
        return False
    # CallMeBot renders plain text; keep it short so nothing is truncated.
    text = text[:900]
    params = {"phone": WHATSAPP_PHONE, "text": text, "apikey": CALLMEBOT_APIKEY}
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(_API, params=params)
        if r.status_code == 200:
            log.info("whatsapp notify sent (%d chars)", len(text))
            return True
        log.warning("whatsapp notify HTTP %s: %s", r.status_code, r.text[:200])
        return False
    except Exception as e:
        log.warning("whatsapp notify failed: %s", e)
        return False
