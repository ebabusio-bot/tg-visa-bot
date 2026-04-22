# -*- coding: utf-8 -*-
"""Telegram bot: US immigration assistant for EB-1A / EB-2 NIW / O-1."""
import html
import logging
import os
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
    "quiz:eb1a":   "Выбрал квиз: EB-1A",
    "quiz:niw":    "Выбрал квиз: EB-2 NIW",
    "quiz:o1":     "Выбрал квиз: O-1",
    "quiz:e2":     "Выбрал квиз: E-2",
    "lang":        "🌐 Сменить язык",
}

async def notify_admin_activity(bot, user, label: str, lang: str | None = None):
    """Send admin notification with a clickable mention link so admin can DM the user."""
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

    saved_lang = db.get_user_lang(u.id)
    await notify_admin_activity(ctx.bot, u, "Отправил /start", saved_lang)

    if not saved_lang:
        # First-time user or not yet chosen — show multilingual language picker.
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
        await q.edit_message_text(t("language_saved", new_lang),
                                  parse_mode=ParseMode.MARKDOWN)
        await ctx.bot.send_message(
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
    # Translate verdict for non-Russian users.
    if lang != "ru":
        try:
            verdict_user = await llm.translate(verdict_ru, lang)
        except Exception:
            log.exception("verdict translation failed; falling back to Russian")
            verdict_user = verdict_ru
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
    if not saved_lang:
        # User hasn't chosen language yet — prompt them before anything else.
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
    if not saved_lang:
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
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    app.add_handler(MessageHandler(
        filters.Document.ALL | filters.PHOTO | filters.VOICE |
        filters.VIDEO | filters.AUDIO | filters.VIDEO_NOTE,
        on_attachment,
    ))
    app.add_error_handler(on_error)
    log.info("Bot started. Model=%s, daily_limit=%d", llm.MODEL, DAILY_LIMIT)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
