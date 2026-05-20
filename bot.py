# -*- coding: utf-8 -*-
"""Telegram bot: US immigration assistant for EB-1A / EB-2 NIW / O-1."""
import html
import logging
import os
import time as _time
from datetime import time as dt_time
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest, Conflict, NetworkError, TimedOut
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)
from telegram.helpers import escape_markdown

import db
import llm
import quiz
import i18n
from i18n import t, LANGUAGES, LANG_FLAGS, LANG_NAMES_RU, normalize_lang

load_dotenv()

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"].strip()
ADMIN_CHAT_ID = int(os.environ["ADMIN_CHAT_ID"].strip())
DAILY_LIMIT = 15

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("bot")

S_MODE      = "mode"
S_QUIZ_KIND = "quiz_kind"
S_QUIZ_IDX  = "quiz_idx"
S_QUIZ_ANS  = "quiz_answers"

def md_esc(s: str | None) -> str:
    """Escape user-provided text for safe inclusion in Markdown (v1) messages."""
    if not s:
        return ""
    return escape_markdown(str(s), version=1)

def fmt_user_md(u) -> str:
    """Markdown-v1 user descriptor with clickable name + id (opens DM/profile)."""
    name = md_esc(u.first_name) or "—"
    if u.username:
        uname_md = f"[@{u.username}](https://t.me/{u.username})"
    else:
        uname_md = "—"
    return (
        f"[{name}](tg://user?id={u.id}) "
        f"({uname_md}, id [{u.id}](tg://user?id={u.id}))"
    )

TG_MSG_SAFE = 3900  # Telegram limit is 4096; leave headroom for footer/markup

def split_for_telegram(text: str, limit: int = TG_MSG_SAFE) -> list[str]:
    """Split text into chunks ≤ limit chars, preferring paragraph boundaries."""
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    current = ""
    for para in text.split("\n\n"):
        candidate = (current + "\n\n" + para) if current else para
        if len(candidate) <= limit:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(para) <= limit:
                current = para
            else:
                for i in range(0, len(para), limit):
                    piece = para[i:i + limit]
                    if i + limit >= len(para):
                        current = piece
                    else:
                        chunks.append(piece)
                        current = ""
    if current:
        chunks.append(current)
    return chunks

async def safe_reply(message, text: str, **kwargs):
    """reply_text with Markdown; on parse failure, resend as plain text."""
    try:
        return await message.reply_text(text, **kwargs)
    except BadRequest as e:
        if "parse" not in str(e).lower() and "entit" not in str(e).lower():
            raise
        log.warning("markdown reply failed, retrying as plain text: %s", e)
        kwargs.pop("parse_mode", None)
        return await message.reply_text(text, **kwargs)

async def safe_send(bot, chat_id: int, text: str, **kwargs):
    """bot.send_message with Markdown; on parse failure, resend as plain text."""
    try:
        return await bot.send_message(chat_id, text, **kwargs)
    except BadRequest as e:
        if "parse" not in str(e).lower() and "entit" not in str(e).lower():
            raise
        log.warning("markdown send failed, retrying as plain text: %s", e)
        kwargs.pop("parse_mode", None)
        return await bot.send_message(chat_id, text, **kwargs)

def user_lang(user_id: int) -> str:
    """Return saved language code for user, or DEFAULT_LANG ('ru') if not set."""
    return normalize_lang(db.get_user_lang(user_id))

def lang_badge(lang: str) -> str:
    """Admin-facing language badge, e.g. '🇬🇧 английский'."""
    flag = LANG_FLAGS.get(lang, "🏳️")
    name = LANG_NAMES_RU.get(lang, lang)
    return f"{flag} {name}"

# Admin-facing labels for callback buttons. Stay in Russian regardless of user language.
CLICK_LABELS = {
    "menu":        "⬅️ В меню",
    "ask":         "❓ Задать вопрос по визе",
    "quiz":        "📋 Оценить шансы (анкета)",
    "case_review": "🆓 Бесплатный разбор ситуации",
    "pricing":     "💰 Стоимость и сроки",
    "book":        "📞 Записаться на консультацию",
    "case_done":   "✅ Завершить отправку (case review)",
    "support":     "🛠 Обратиться в техподдержку",
    "quiz:eb1a":   "Выбрал квиз: EB-1A",
    "quiz:niw":    "Выбрал квиз: EB-2 NIW",
    "quiz:o1":     "Выбрал квиз: O-1",
    "quiz:e2":     "Выбрал квиз: E-2",
    "lang":        "🌐 Сменить язык",
}

async def notify_admin_activity(bot, user, label: str, lang: str | None = None,
                                event_label: str | None = None):
    """Send admin notification with a clickable mention link so admin can DM the user.
    Also records the click/start event in DB for analytics.

    `label` is the admin-facing text (may include extras like a traffic source);
    `event_label` is the canonical label used to classify the event type — pass it
    when `label` is decorated, otherwise `label` itself is used."""
    classify = event_label or label
    try:
        event_type = "start" if classify == "Отправил /start" else "click"
        db.log_event(user.id, event_type, classify)
    except Exception as e:
        log.warning("db.log_event FAILED: %s (user=%s label=%s)", e, user.id, label)
    try:
        name = html.escape(user.first_name or "—")
        if user.username:
            uname_html = f'<a href="https://t.me/{user.username}">@{user.username}</a>'
        else:
            uname_html = "—"
        mention = f'<a href="tg://user?id={user.id}">{name}</a>'
        id_link = f'<a href="tg://user?id={user.id}">{user.id}</a>'
        lang_tag = ""
        if lang:
            lang_tag = f"\n<i>{html.escape(lang_badge(lang))}</i>"
        text = (
            f"👆 {mention} ({uname_html}, id {id_link})\n"
            f"{html.escape(label)}{lang_tag}"
        )
        await bot.send_message(ADMIN_CHAT_ID, text, parse_mode=ParseMode.HTML,
                               disable_web_page_preview=True)
        log.info("admin activity notify sent: user=%s label=%s", user.id, label)
    except Exception as e:
        log.warning("admin activity notify FAILED: %s (user=%s label=%s)",
                    e, user.id, label)

async def notify_admin_conversation(bot, user, user_msg: str, bot_answer: str, lang: str):
    """Forward a user's question and the bot's LLM answer to the admin, in real time,
    so the admin sees exactly what clients are being told. Two messages:
      1) header + user's question (escaped, admin language = Russian)
      2) bot's answer, preserving its own Markdown; split if over Telegram limit."""
    try:
        header = (
            f"💬 *Диалог* · {fmt_user_md(user)} · {md_esc(lang_badge(lang))}\n\n"
            f"*👤 Вопрос пользователя:*\n{md_esc(user_msg)}"
        )
        await safe_send(bot, ADMIN_CHAT_ID, header, parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True)
        answer_body = "🤖 *Ответ бота:*\n\n" + bot_answer
        for part in split_for_telegram(answer_body):
            await safe_send(bot, ADMIN_CHAT_ID, part, parse_mode=ParseMode.MARKDOWN,
                            disable_web_page_preview=True)
        log.info("admin conversation notify sent: user=%s q_chars=%d a_chars=%d",
                 user.id, len(user_msg), len(bot_answer))
    except Exception as e:
        log.warning("admin conversation notify FAILED: %s (user=%s)", e, user.id)

# ────────────────────────────────────────────────────────────── keyboards

def language_kb() -> InlineKeyboardMarkup:
    """Keyboard with flag+native-name buttons for every supported language.
    Arranged in 2 columns, last row may have a single button."""
    rows = []
    row = []
    for code, flag, native in LANGUAGES:
        row.append(InlineKeyboardButton(f"{flag} {native}", callback_data=f"setlang:{code}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(rows)

def main_menu_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_ask", lang),         callback_data="ask")],
        [InlineKeyboardButton(t("btn_quiz", lang),        callback_data="quiz")],
        [InlineKeyboardButton(t("btn_case_review", lang), callback_data="case_review")],
        [InlineKeyboardButton(t("btn_pricing", lang),     callback_data="pricing")],
        [InlineKeyboardButton(t("btn_book", lang),        callback_data="book")],
        [InlineKeyboardButton(t("btn_support", lang),     callback_data="support")],
        [InlineKeyboardButton(t("btn_lang", lang),        callback_data="lang")],
    ])

def case_review_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_case_done", lang), callback_data="case_done")],
        [InlineKeyboardButton(t("btn_back", lang),      callback_data="menu")],
    ])

def quiz_select_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_quiz_eb1a", lang), callback_data="quiz:eb1a")],
        [InlineKeyboardButton(t("btn_quiz_niw",  lang), callback_data="quiz:niw")],
        [InlineKeyboardButton(t("btn_quiz_o1",   lang), callback_data="quiz:o1")],
        [InlineKeyboardButton(t("btn_quiz_e2",   lang), callback_data="quiz:e2")],
        [InlineKeyboardButton(t("btn_back",      lang), callback_data="menu")],
    ])

def yes_no_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_yes", lang), callback_data="q:yes"),
        InlineKeyboardButton(t("btn_no",  lang), callback_data="q:no"),
    ]])

def post_quiz_kb(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_book", lang), callback_data="book")],
        [InlineKeyboardButton(t("btn_back", lang), callback_data="menu")],
    ])

# ────────────────────────────────────────────────────────────── commands

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    db.upsert_user(u.id, u.username, u.first_name)
    ctx.user_data.clear()

    # Deep-link traffic source: t.me/SunnyFl_bot?start=instagram → ctx.args == ['instagram']
    source = None
    if ctx.args:
        source = db.set_user_source(u.id, ctx.args[0])

    saved_lang = db.get_user_lang(u.id)
    start_label = "Отправил /start"
    admin_label = start_label
    if source:
        admin_label = f"{start_label} (источник: {source})"
    await notify_admin_activity(ctx.bot, u, admin_label, saved_lang,
                                event_label=start_label)

    if saved_lang not in i18n.LANG_CODES:
        # Either first-time user, or saved language is no longer supported
        # (e.g. a Bengali user from before we trimmed the supported set).
        # Show the picker and let them re-select.
        await update.message.reply_text(
            i18n.LANGUAGE_PICKER_PROMPT,
            reply_markup=language_kb(),
        )
        return

    lang = normalize_lang(saved_lang)
    await update.message.reply_text(
        t("welcome", lang), parse_mode=ParseMode.MARKDOWN,
        reply_markup=main_menu_kb(lang),
    )

async def cmd_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    lang = user_lang(update.effective_user.id)
    await update.message.reply_text(t("menu_header", lang), reply_markup=main_menu_kb(lang))

async def cmd_reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    lang = user_lang(update.effective_user.id)
    await update.message.reply_text(
        t("context_reset", lang),
        reply_markup=main_menu_kb(lang),
    )

async def cmd_lang(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Change language."""
    await update.message.reply_text(
        i18n.LANGUAGE_PICKER_PROMPT,
        reply_markup=language_kb(),
    )

async def cmd_whoami(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Diagnostic: show user's Telegram ID and whether it matches ADMIN_CHAT_ID."""
    u = update.effective_user
    is_admin = u and u.id == ADMIN_CHAT_ID
    lang = db.get_user_lang(u.id) or "—"
    await update.message.reply_text(
        f"Ваш Telegram user ID: {u.id}\n"
        f"ADMIN ID в настройках бота: {ADMIN_CHAT_ID}\n"
        f"Совпадают: {'✅ да (вы админ)' if is_admin else '❌ нет'}\n"
        f"Язык: {lang}"
    )

async def cmd_testnotify(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Admin-only: force a test admin-activity notification and report success/failure."""
    if not _is_admin(update):
        return
    u = update.effective_user
    try:
        await ctx.bot.send_message(
            ADMIN_CHAT_ID,
            f"🔔 Тестовое уведомление\nОт /testnotify, user id {u.id}"
        )
        await update.message.reply_text(
            "✅ Тестовое уведомление отправлено. Если выше видно сообщение «🔔 Тестовое уведомление» — "
            "пайплайн работает."
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка при отправке уведомления: {type(e).__name__}: {e}"
        )

def _is_admin(update: Update) -> bool:
    u = update.effective_user
    c = update.effective_chat
    return bool(
        (u and u.id == ADMIN_CHAT_ID) or (c and c.id == ADMIN_CHAT_ID)
    )

async def cmd_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return
    rows = db.list_users_with_stats(limit=50)
    if not rows:
        await update.message.reply_text("Пользователей пока нет.")
        return
    lines = ["Пользователи бота (последние 50):\n"]
    for r in rows:
        name = r["first_name"] or "—"
        uname = f"@{r['username']}" if r["username"] else "—"
        last = (r["last_msg"] or "—")[:16]
        lines.append(
            f"{r['tg_id']} · {name} · {uname}\n"
            f"   сообщений: {r['msg_count']} · последнее: {last}"
        )
    lines.append("\nЧтобы посмотреть переписку: /chat <id>")
    await update.message.reply_text("\n".join(lines))

async def cmd_chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return
    if not ctx.args:
        await update.message.reply_text(
            "Использование: /chat <tg_id>\nID берите из /users."
        )
        return
    try:
        tg_id = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("ID должен быть числом.")
        return
    msgs = db.full_history(tg_id, limit=100)
    if not msgs:
        await update.message.reply_text(f"С пользователем {tg_id} переписки нет.")
        return
    chunks: list[str] = [f"Переписка с {tg_id} (до 100 сообщ.):\n"]
    for m in msgs:
        who = "👤" if m["role"] == "user" else "🤖"
        ts = (m["created_at"] or "")[:16]
        body = m["content"] or ""
        chunks.append(f"{who} {ts}\n{body}\n")
    text = "\n".join(chunks)
    for i in range(0, len(text), 3500):
        await update.message.reply_text(text[i:i + 3500])

async def cmd_leads(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return
    rows = db.list_leads(limit=30)
    if not rows:
        await update.message.reply_text("Заявок пока нет.")
        return
    lines = ["Последние заявки (до 30):\n"]
    for r in rows:
        ts = (r["created_at"] or "")[:16]
        uname = f"@{r['username']}" if r["username"] else "—"
        src = r["source"] or "—"
        payload = (r["payload"] or "")[:200]
        lines.append(
            f"{ts} · {src} · {uname} · {r['tg_id']}\n{payload}\n"
        )
    text = "\n".join(lines)
    for i in range(0, len(text), 3500):
        await update.message.reply_text(text[i:i + 3500])

# ────────────────────────────────────────────────────────────── analytics

ADMIN_TZ = ZoneInfo("Europe/Moscow")

def _format_stats(days: int, title: str) -> str:
    """Build a human-readable stats summary block for /stats and daily report."""
    s = db.stats_summary(days)
    quiz_conv = ""
    if s["quiz_starts"]:
        pct = 100 * s["quiz_finishes"] // s["quiz_starts"]
        quiz_conv = f" ({pct}% завершено)"
    start_to_lead = ""
    if s["starts"]:
        pct = 100 * s["leads"] // s["starts"]
        start_to_lead = f"\n• Конверсия /start → заявка: {pct}%"
    by_kind = "—"
    if s["by_kind"]:
        by_kind = ", ".join(f"{r['payload']}: {r['n']}" for r in s["by_kind"])
    by_source = "—"
    if s["by_source"]:
        by_source = ", ".join(f"{r['source']}: {r['n']}" for r in s["by_source"])
    by_lang = "—"
    if s["by_lang"]:
        by_lang = ", ".join(f"{r['lang']}: {r['n']}" for r in s["by_lang"])
    by_traffic = "—"
    if s.get("by_traffic"):
        by_traffic = "\n".join(f"  • {r['source']}: {r['n']}" for r in s["by_traffic"])
    return (
        f"📊 *{title}*\n\n"
        f"👤 *Пользователи:*\n"
        f"• /start (всего за период): {s['starts']}\n"
        f"• Новых юзеров: {s['new_users']}\n"
        f"• Всего в базе: {s['total_users']}\n\n"
        f"📋 *Квизы:*\n"
        f"• Начали: {s['quiz_starts']}\n"
        f"• Завершили: {s['quiz_finishes']}{quiz_conv}\n"
        f"• По категориям: {by_kind}\n\n"
        f"💬 *Q&A:* {s['qa_asks']} вопросов\n\n"
        f"📞 *Заявки:* {s['leads']}\n"
        f"• По кнопкам: {by_source}"
        f"{start_to_lead}\n\n"
        f"📣 *Источники переходов (новые юзеры):*\n{by_traffic}\n\n"
        f"🌐 *Новые юзеры по языкам:* {by_lang}"
    )

async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Admin-only: show funnel statistics for today / 7 days / all time."""
    if not _is_admin(update):
        return
    today = _format_stats(0, "Сегодня")
    week = _format_stats(7, "За 7 дней")
    all_time = _format_stats(36500, "За всё время")
    for chunk in (today, week, all_time):
        await update.message.reply_text(chunk, parse_mode=ParseMode.MARKDOWN)

KIND_NAMES = {"eb1a": "EB-1A", "niw": "EB-2 NIW", "o1": "O-1", "e2": "E-2"}

async def send_quiz_reminder(bot, tg_id: int, kind: str, stage: int):
    """Send a 'finish your quiz' reminder to the user in their language."""
    user_row = db.get_user_for_reminder(tg_id)
    lang = (user_row and user_row.get("lang")) or "ru"
    kind_name = KIND_NAMES.get(kind, kind.upper())
    text = t("reminder_quiz_incomplete", lang).format(kind=kind_name)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_reminder_resume", lang), callback_data=f"quiz:{kind}"),
        InlineKeyboardButton(t("btn_back", lang),            callback_data="menu"),
    ]])
    try:
        await bot.send_message(tg_id, text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        db.mark_reminded(tg_id, kind, stage)
        log.info("reminder sent: user=%s kind=%s stage=%d", tg_id, kind, stage)
    except Exception as e:
        # User may have blocked the bot. Still mark as reminded so we don't retry forever.
        db.mark_reminded(tg_id, kind, stage)
        log.warning("reminder FAILED: user=%s kind=%s stage=%d err=%s",
                    tg_id, kind, stage, e)

async def job_check_reminders(ctx: ContextTypes.DEFAULT_TYPE):
    """Periodic job: find users with stale unfinished quizzes and remind them."""
    for stage in (1, 2):
        for row in db.find_pending_reminders(stage):
            await send_quiz_reminder(ctx.bot, row["tg_id"], row["kind"], stage)

async def send_reengagement(bot, tg_id: int):
    """Send a 'come back' reminder to a user who visited but didn't return."""
    user_row = db.get_user_for_reminder(tg_id)
    lang = (user_row and user_row.get("lang")) or "ru"
    text = t("reminder_reengagement", lang)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(t("btn_ask", lang),  callback_data="ask"),
        InlineKeyboardButton(t("btn_back", lang), callback_data="menu"),
    ]])
    try:
        await bot.send_message(tg_id, text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        log.info("re-engagement sent: user=%s", tg_id)
    except Exception as e:
        log.warning("re-engagement FAILED: user=%s err=%s", tg_id, e)
    finally:
        # Mark regardless of success so we never spam-retry a blocked user.
        db.mark_reengaged(tg_id)

async def job_check_reengagement(ctx: ContextTypes.DEFAULT_TYPE):
    """Periodic job: remind users who visited yesterday but didn't come back."""
    for tg_id in db.find_reengagement_targets():
        await send_reengagement(ctx.bot, tg_id)

async def send_lead_followup(bot, tg_id: int):
    """Warm up a user who left a lead but hasn't been closed yet."""
    user_row = db.get_user_for_reminder(tg_id)
    lang = (user_row and user_row.get("lang")) or "ru"
    text = t("reminder_lead_followup", lang)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(t("btn_book", lang), callback_data="book")],
        [InlineKeyboardButton(t("btn_ask", lang),  callback_data="ask")],
        [InlineKeyboardButton(t("btn_back", lang), callback_data="menu")],
    ])
    try:
        await bot.send_message(tg_id, text, reply_markup=kb, parse_mode=ParseMode.MARKDOWN)
        log.info("lead follow-up sent: user=%s", tg_id)
    except Exception as e:
        log.warning("lead follow-up FAILED: user=%s err=%s", tg_id, e)
    finally:
        db.mark_lead_followup(tg_id)

async def job_check_lead_followup(ctx: ContextTypes.DEFAULT_TYPE):
    """Periodic job: warm up users who left a lead 24-48h ago."""
    for tg_id in db.find_lead_followup_targets():
        await send_lead_followup(ctx.bot, tg_id)

# ─── heartbeat (consumed by the standalone healthcheck.py service) ──────────

HEARTBEAT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "heartbeat")

def _touch_heartbeat():
    """Update the heartbeat file's mtime. The separate healthcheck service
    reads this file's age; keeping it in its own service means bot restarts
    (deploys) don't cause false 'down' alerts."""
    try:
        with open(HEARTBEAT_FILE, "w") as f:
            f.write(str(_time.time()))
    except Exception as e:
        log.warning("heartbeat write failed: %s", e)

async def job_heartbeat(ctx: ContextTypes.DEFAULT_TYPE):
    """Refresh the heartbeat file; proves the asyncio event loop is alive."""
    _touch_heartbeat()

async def job_daily_summary(ctx: ContextTypes.DEFAULT_TYPE):
    """Daily 09:00 MSK admin report covering yesterday's full day."""
    text = _format_stats(1, "Сводка за последние 24 часа")
    try:
        await ctx.bot.send_message(ADMIN_CHAT_ID, text, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        log.warning("daily summary FAILED: %s", e)

# ────────────────────────────────────────────────────────────── callbacks

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    u = q.from_user
    lang = user_lang(u.id)

    # Language selection (before main menu is even visible)
    if data.startswith("setlang:"):
        new_lang = normalize_lang(data.split(":", 1)[1])
        db.upsert_user(u.id, u.username, u.first_name)
        db.set_user_lang(u.id, new_lang)
        await notify_admin_activity(
            ctx.bot, u, f"Выбрал язык: {lang_badge(new_lang)}", new_lang,
        )
        # Replace the picker with confirmation and then send welcome + menu.
        try:
            await q.edit_message_text(t("language_saved", new_lang),
                                      parse_mode=ParseMode.MARKDOWN)
        except BadRequest:
            # Fallback if the picker message is no longer editable.
            log.info("could not edit language picker message; sending fresh confirmation")
        await safe_send(
            ctx.bot,
            q.message.chat_id,
            t("welcome", new_lang),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=main_menu_kb(new_lang),
        )
        return

    if not data.startswith("q:"):
        label = CLICK_LABELS.get(data, f"нажал кнопку: {data}")
        await notify_admin_activity(ctx.bot, u, label, lang)

    if data == "menu":
        ctx.user_data.clear()
        await q.edit_message_text(t("menu_header", lang), reply_markup=main_menu_kb(lang))
        return

    if data == "lang":
        await q.edit_message_text(
            i18n.LANGUAGE_PICKER_PROMPT,
            reply_markup=language_kb(),
        )
        return

    if data == "ask":
        ctx.user_data[S_MODE] = None
        left = max(0, DAILY_LIMIT - db.get_today_count(u.id))
        await q.edit_message_text(
            t("ask_prompt", lang).format(left=left, total=DAILY_LIMIT),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data == "quiz":
        ctx.user_data[S_MODE] = None
        await q.edit_message_text(t("quiz_start", lang), reply_markup=quiz_select_kb(lang))
        return

    if data.startswith("quiz:"):
        kind = data.split(":", 1)[1]
        cfg = quiz.get_quiz(kind, lang)
        if not cfg:
            await q.edit_message_text(
                t("unknown_quiz", lang), reply_markup=main_menu_kb(lang)
            )
            return
        ctx.user_data[S_MODE]      = "quiz"
        ctx.user_data[S_QUIZ_KIND] = kind
        ctx.user_data[S_QUIZ_IDX]  = 0
        ctx.user_data[S_QUIZ_ANS]  = []
        db.start_quiz(q.from_user.id, kind)
        db.log_event(q.from_user.id, "quiz_start", kind)
        await q.edit_message_text(cfg["intro"], parse_mode=ParseMode.MARKDOWN)
        await ctx.bot.send_message(
            q.message.chat_id,
            t("quiz_q_header", lang).format(n=1, total=cfg["total"], q=cfg["questions"][0]),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=yes_no_kb(lang),
        )
        return

    if data.startswith("q:"):
        await handle_quiz_answer(update, ctx, data == "q:yes")
        return

    if data == "book":
        ctx.user_data[S_MODE] = "lead"
        await q.edit_message_text(t("lead_prompt", lang), parse_mode=ParseMode.MARKDOWN)
        return

    if data == "pricing":
        ctx.user_data[S_MODE] = None
        await q.edit_message_text(
            t("pricing", lang),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t("btn_book", lang), callback_data="book")],
                [InlineKeyboardButton(t("btn_back", lang), callback_data="menu")],
            ]),
        )
        return

    if data == "case_review":
        ctx.user_data[S_MODE] = "case_review"
        ctx.user_data["case_review_started"] = False
        await q.edit_message_text(
            t("case_review_info", lang),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=case_review_kb(lang),
        )
        return

    if data == "case_done":
        if ctx.user_data.get(S_MODE) != "case_review":
            await q.edit_message_text(
                t("case_button_inactive", lang),
                reply_markup=main_menu_kb(lang),
            )
            return
        db.save_lead(u.id, u.username, "Бесплатный разбор кейса (см. пересланные сообщения)", "case_review")
        try:
            await safe_send(
                ctx.bot,
                ADMIN_CHAT_ID,
                f"✅ *Завершён сбор материалов* для бесплатного разбора\n\n"
                f"От: {fmt_user_md(u)}\n"
                f"Язык: {md_esc(lang_badge(lang))}\n"
                f"_Все его сообщения и документы пересланы выше._",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            log.warning("admin notify failed: %s", e)
        ctx.user_data[S_MODE] = None
        ctx.user_data.pop("case_review_started", None)
        await q.edit_message_text(
            t("case_review_done", lang),
            reply_markup=main_menu_kb(lang),
        )
        return

    if data == "support":
        ctx.user_data[S_MODE] = "support"
        await q.edit_message_text(
            t("support_info", lang),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(t("btn_back", lang), callback_data="menu")],
            ]),
        )
        return

async def handle_quiz_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE, is_yes: bool):
    q = update.callback_query
    u = q.from_user
    lang = user_lang(u.id)
    kind = ctx.user_data.get(S_QUIZ_KIND)
    idx  = ctx.user_data.get(S_QUIZ_IDX, 0)
    ans  = ctx.user_data.get(S_QUIZ_ANS, [])
    cfg  = quiz.get_quiz(kind, lang)
    if not cfg:
        await q.edit_message_text(
            t("quiz_not_active", lang),
            reply_markup=main_menu_kb(lang),
        )
        return

    # Notify admin of each yes/no answer so the whole quiz progress is visible.
    answer_mark = "✅ Да" if is_yes else "❌ Нет"
    await notify_admin_activity(
        ctx.bot, u,
        f"📋 Квиз {kind.upper()} · В{idx + 1}/{cfg['total']} · {answer_mark}",
        lang,
    )

    ans.append(is_yes)
    idx += 1
    ctx.user_data[S_QUIZ_ANS] = ans
    ctx.user_data[S_QUIZ_IDX] = idx

    if idx < cfg["total"]:
        await q.edit_message_text(
            t("quiz_q_header", lang).format(n=idx + 1, total=cfg["total"], q=cfg["questions"][idx]),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=yes_no_kb(lang),
        )
        return

    verdict_ru, qualifies = quiz.summarize(kind, ans)
    db.finish_quiz(u.id, kind)
    db.log_event(u.id, "quiz_finish", f"{kind}:{sum(ans)}/{cfg['total']}")
    # Translate verdict for non-Russian users.
    if lang != "ru":
        try:
            verdict_user = await llm.translate(verdict_ru, lang)
        except Exception:
            log.exception("verdict translation failed; falling back to Russian + note")
            # Prepend a short English note so a non-RU reader at least
            # knows why the text is in Cyrillic, and can tap the book button.
            verdict_user = (
                "_⚠️ Translation service is temporarily unavailable — the verdict "
                "is shown in Russian. Tap below to book a consultation or open the menu._\n\n"
                + verdict_ru
            )
    else:
        verdict_user = verdict_ru
    ctx.user_data[S_MODE] = None

    # Admin report: always in Russian, use RU questions from prompts.
    import prompts as _p
    questions_ru = {
        "eb1a": _p.EB1A_QUESTIONS, "niw": _p.NIW_QUESTIONS,
        "o1":   _p.O1_QUESTIONS,   "e2":  _p.E2_QUESTIONS,
    }.get(kind, cfg["questions"])
    detail = "\n".join(
        f"{'✅' if a else '❌'} {questions_ru[i]}"
        for i, a in enumerate(ans)
    )
    admin_txt = (
        f"📋 *Квалификационная анкета завершена*\n\n"
        f"Пользователь: {fmt_user_md(u)}\n"
        f"Язык: {md_esc(lang_badge(lang))}\n"
        f"Виза: *{md_esc(kind.upper())}*\n"
        f"Результат: {sum(ans)}/{cfg['total']} — "
        f"{'✅ квалифицируется' if qualifies else '⚠️ под вопросом'}\n\n"
        f"{md_esc(detail)}"
    )
    try:
        await safe_send(ctx.bot, ADMIN_CHAT_ID, admin_txt, parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        log.warning("admin notify failed: %s", e)
    db.save_lead(u.id, u.username, f"{kind}: {sum(ans)}/{cfg['total']}", "quiz")

    await q.edit_message_text(verdict_user, parse_mode=ParseMode.MARKDOWN,
                              reply_markup=post_quiz_kb(lang))

# ────────────────────────────────────────────────────────────── messages

async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    db.upsert_user(u.id, u.username, u.first_name)

    saved_lang = db.get_user_lang(u.id)
    if saved_lang not in i18n.LANG_CODES:
        # Not chosen yet, or previously chosen a now-unsupported language.
        await update.message.reply_text(
            i18n.LANGUAGE_PICKER_PROMPT,
            reply_markup=language_kb(),
        )
        return
    lang = normalize_lang(saved_lang)

    text = update.message.text.strip()
    mode = ctx.user_data.get(S_MODE)

    if mode == "quiz":
        await update.message.reply_text(
            t("in_quiz_warning", lang),
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if mode == "lead":
        db.save_lead(u.id, u.username, text, "booking")
        ctx.user_data[S_MODE] = None
        admin_txt = (
            f"📞 *Новая заявка на консультацию*\n\n"
            f"От: {fmt_user_md(u)}\n"
            f"Язык: {md_esc(lang_badge(lang))}\n\n"
            f"{md_esc(text)}"
        )
        try:
            await safe_send(ctx.bot, ADMIN_CHAT_ID, admin_txt, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            log.warning("admin notify failed: %s", e)
        await update.message.reply_text(t("lead_received", lang), reply_markup=main_menu_kb(lang))
        return

    if mode == "case_review":
        await _forward_case_review(update, ctx, "text")
        return

    if mode == "support":
        await _forward_support(update, ctx)
        return

    allowed, new_count = db.try_consume_daily(u.id, DAILY_LIMIT)
    if not allowed:
        await update.message.reply_text(
            t("limit_reached", lang),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(t("btn_book", lang), callback_data="book")
            ]]),
        )
        return

    await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

    db.log_event(u.id, "qa_ask")
    history = db.recent_history(u.id, limit=8)
    try:
        answer, offer_consultation = await llm.ask(history, text, lang)
    except Exception:
        log.exception("LLM error")
        db.save_msg(u.id, "user", text)
        await update.message.reply_text(t("llm_error", lang))
        return

    db.save_msg(u.id, "user", text)
    db.save_msg(u.id, "assistant", answer)

    left = DAILY_LIMIT - new_count
    footer = t("footer_remaining", lang).format(left=left, total=DAILY_LIMIT)

    kb = None
    if offer_consultation:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(t("btn_book",        lang), callback_data="book")],
            [InlineKeyboardButton(t("btn_case_review", lang), callback_data="case_review")],
            [InlineKeyboardButton(t("btn_back",        lang), callback_data="menu")],
        ])

    parts = split_for_telegram(answer)
    for part in parts[:-1]:
        await safe_reply(update.message, part, parse_mode=ParseMode.MARKDOWN)
    last = parts[-1] + footer
    await safe_reply(
        update.message, last,
        parse_mode=ParseMode.MARKDOWN, reply_markup=kb,
    )

    # Forward the Q&A pair to admin so she can see what clients are told.
    await notify_admin_conversation(ctx.bot, u, text, answer, lang)

async def _forward_case_review(update: Update, ctx: ContextTypes.DEFAULT_TYPE, kind: str):
    """Forward a user's text/document/photo to the admin during case_review mode."""
    u = update.effective_user
    db.upsert_user(u.id, u.username, u.first_name)
    lang = user_lang(u.id)

    if not ctx.user_data.get("case_review_started"):
        try:
            await safe_send(
                ctx.bot,
                ADMIN_CHAT_ID,
                f"🆓 *Новая заявка на бесплатный разбор*\n\n"
                f"От: {fmt_user_md(u)}\n"
                f"Язык: {md_esc(lang_badge(lang))}\n"
                f"_Ниже пересылаются его сообщения и документы:_",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            log.warning("admin notify failed: %s", e)
        ctx.user_data["case_review_started"] = True

    forwarded = True
    try:
        await ctx.bot.forward_message(
            chat_id=ADMIN_CHAT_ID,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
        )
    except Exception as e:
        forwarded = False
        log.warning("forward failed: %s", e)

    if forwarded:
        await update.message.reply_text(
            t("case_review_forwarded", lang),
            reply_markup=case_review_kb(lang),
        )
    else:
        await update.message.reply_text(
            t("case_review_forward_failed", lang),
            reply_markup=case_review_kb(lang),
        )

async def _forward_support(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Forward a user's tech-support message/attachment to the admin, then exit
    support mode. One message per request — to send more, the user taps again."""
    u = update.effective_user
    db.upsert_user(u.id, u.username, u.first_name)
    lang = user_lang(u.id)

    delivered = True
    try:
        await safe_send(
            ctx.bot,
            ADMIN_CHAT_ID,
            f"🛠 *Обращение в техподдержку*\n\n"
            f"От: {fmt_user_md(u)}\n"
            f"Язык: {md_esc(lang_badge(lang))}\n"
            f"_Сообщение пользователя ниже:_",
            parse_mode=ParseMode.MARKDOWN,
        )
        await ctx.bot.forward_message(
            chat_id=ADMIN_CHAT_ID,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
        )
    except Exception as e:
        delivered = False
        log.warning("support forward failed: %s", e)

    db.save_lead(u.id, u.username,
                 "Обращение в техподдержку (см. пересланное сообщение)", "support")
    db.log_event(u.id, "support")
    ctx.user_data[S_MODE] = None
    key = "support_sent" if delivered else "support_failed"
    await update.message.reply_text(t(key, lang), reply_markup=main_menu_kb(lang))

async def _forward_booking_attachment(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Forward attachment sent during lead (booking) mode to the admin."""
    u = update.effective_user
    db.upsert_user(u.id, u.username, u.first_name)
    lang = user_lang(u.id)
    db.save_lead(u.id, u.username, "Файл приложен к заявке (см. пересланное сообщение)", "booking_file")
    try:
        await safe_send(
            ctx.bot,
            ADMIN_CHAT_ID,
            f"📎 *Файл к заявке на консультацию*\n\n"
            f"От: {fmt_user_md(u)}\n"
            f"Язык: {md_esc(lang_badge(lang))}\n"
            f"_Файл пересылается ниже._",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as e:
        log.warning("admin notify failed: %s", e)

    forwarded = True
    try:
        await ctx.bot.forward_message(
            chat_id=ADMIN_CHAT_ID,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
        )
    except Exception as e:
        forwarded = False
        log.warning("forward failed: %s", e)

    if forwarded:
        await update.message.reply_text(t("booking_file_ok", lang))
    else:
        await update.message.reply_text(t("booking_file_failed", lang))

async def on_attachment(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle non-text messages (documents/photos/voice/video/audio)."""
    u = update.effective_user
    saved_lang = db.get_user_lang(u.id)
    if saved_lang not in i18n.LANG_CODES:
        await update.message.reply_text(
            i18n.LANGUAGE_PICKER_PROMPT,
            reply_markup=language_kb(),
        )
        return
    lang = normalize_lang(saved_lang)

    mode = ctx.user_data.get(S_MODE)
    if mode == "case_review":
        await _forward_case_review(update, ctx, "attachment")
        return
    if mode == "support":
        await _forward_support(update, ctx)
        return
    if mode == "lead":
        await _forward_booking_attachment(update, ctx)
        return
    await update.message.reply_text(
        t("attachment_hint", lang),
        reply_markup=main_menu_kb(lang),
    )

async def on_error(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    log.exception("Update error", exc_info=ctx.error)
    err = ctx.error
    if isinstance(err, (Conflict, NetworkError, TimedOut)):
        return
    try:
        import traceback
        tb = "".join(traceback.format_exception(type(err), err, err.__traceback__))[-2500:]

        user_info = "—"
        action = "—"
        if isinstance(update, Update):
            u = update.effective_user
            if u:
                user_info = f"{u.first_name or ''} (@{u.username or '—'}, id {u.id})"
            if update.callback_query:
                action = f"callback: {update.callback_query.data}"
            elif update.message:
                if update.message.text:
                    action = f"text: {update.message.text[:80]}"
                elif update.message.document:
                    action = "document"
                elif update.message.photo:
                    action = "photo"

        alert = (
            f"⚠️ *Ошибка в боте*\n\n"
            f"*Пользователь:* {user_info}\n"
            f"*Действие:* `{action}`\n"
            f"*Ошибка:* `{type(err).__name__}: {err}`\n\n"
            f"```\n{tb}\n```"
        )
        alert = alert[:4000]
        await ctx.bot.send_message(ADMIN_CHAT_ID, alert, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        log.exception("Failed to send error alert to admin")

def main():
    db.init_db()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("menu",    cmd_menu))
    app.add_handler(CommandHandler("reset",   cmd_reset))
    app.add_handler(CommandHandler("lang",    cmd_lang))
    app.add_handler(CommandHandler("language", cmd_lang))
    app.add_handler(CommandHandler("whoami",      cmd_whoami))
    app.add_handler(CommandHandler("testnotify",  cmd_testnotify))
    app.add_handler(CommandHandler("users",       cmd_users))
    app.add_handler(CommandHandler("chat",    cmd_chat))
    app.add_handler(CommandHandler("leads",   cmd_leads))
    app.add_handler(CommandHandler("stats",   cmd_stats))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(MessageHandler(
        filters.Document.ALL | filters.PHOTO | filters.VOICE |
        filters.VIDEO | filters.AUDIO | filters.VIDEO_NOTE,
        on_attachment,
    ))
    app.add_error_handler(on_error)
    # Write an initial heartbeat right away so the healthcheck service sees
    # the bot as up immediately after a restart.
    _touch_heartbeat()
    # Background jobs: heartbeat every minute, quiz reminders every 30 min,
    # re-engagement hourly, daily summary at 09:00 Moscow time.
    app.job_queue.run_repeating(job_heartbeat, interval=60, first=1)
    app.job_queue.run_repeating(job_check_reminders, interval=1800, first=300)
    app.job_queue.run_repeating(job_check_reengagement, interval=3600, first=600)
    app.job_queue.run_repeating(job_check_lead_followup, interval=3600, first=900)
    app.job_queue.run_daily(job_daily_summary, time=dt_time(9, 0, tzinfo=ADMIN_TZ))
    log.info("Bot started. Model=%s, daily_limit=%d", llm.MODEL, DAILY_LIMIT)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
