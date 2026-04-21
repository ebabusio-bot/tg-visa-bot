# -*- coding: utf-8 -*-
"""Telegram bot: US immigration assistant for EB-1A / EB-2 NIW / O-1."""
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
from prompts import (
    DISCLAIMER, WELCOME, LIMIT_REACHED,
    LEAD_PROMPT, LEAD_RECEIVED, QUIZ_START, PRICING_TEXT,
)

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

def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❓ Задать вопрос по визе",         callback_data="ask")],
        [InlineKeyboardButton("📋 Оценить шансы (анкета)",       callback_data="quiz")],
        [InlineKeyboardButton("🆓 Бесплатный разбор ситуации",   callback_data="case_review")],
        [InlineKeyboardButton("💰 Стоимость и сроки",            callback_data="pricing")],
        [InlineKeyboardButton("📞 Записаться на консультацию",   callback_data="book")],
    ])

def case_review_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Завершить отправку", callback_data="case_done")],
        [InlineKeyboardButton("⬅️ В меню",            callback_data="menu")],
    ])

def quiz_select_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("EB-1A (Extraordinary Ability)",  callback_data="quiz:eb1a")],
        [InlineKeyboardButton("EB-2 NIW (National Interest)",   callback_data="quiz:niw")],
        [InlineKeyboardButton("O-1 (Extraordinary Ability)",    callback_data="quiz:o1")],
        [InlineKeyboardButton("E-2 (Treaty Investor)",          callback_data="quiz:e2")],
        [InlineKeyboardButton("⬅️ В меню", callback_data="menu")],
    ])

def yes_no_kb():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Да",  callback_data="q:yes"),
        InlineKeyboardButton("❌ Нет", callback_data="q:no"),
    ]])

def post_quiz_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Записаться на консультацию", callback_data="book")],
        [InlineKeyboardButton("⬅️ В меню", callback_data="menu")],
    ])

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    db.upsert_user(u.id, u.username, u.first_name)
    ctx.user_data.clear()
    await update.message.reply_text(
        WELCOME, parse_mode=ParseMode.MARKDOWN, reply_markup=main_menu_kb()
    )

async def cmd_menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("Главное меню:", reply_markup=main_menu_kb())

async def cmd_reset(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    await update.message.reply_text("Контекст сброшен. /menu — главное меню.")

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

async def on_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "menu":
        ctx.user_data.clear()
        await q.edit_message_text("Главное меню:", reply_markup=main_menu_kb())
        return

    if data == "ask":
        ctx.user_data[S_MODE] = None
        left = max(0, DAILY_LIMIT - db.get_today_count(q.from_user.id))
        await q.edit_message_text(
            "Задайте ваш вопрос по EB-1A, EB-2 NIW, O-1, E-2 или убежищу. "
            "Отвечаю на основе правил USCIS.\n\n"
            f"_Осталось сообщений сегодня: {left}/{DAILY_LIMIT}_",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if data == "quiz":
        ctx.user_data[S_MODE] = None
        await q.edit_message_text(QUIZ_START, reply_markup=quiz_select_kb())
        return

    if data.startswith("quiz:"):
        kind = data.split(":", 1)[1]
        cfg = quiz.get_quiz(kind)
        if not cfg:
            await q.edit_message_text(
                "Неизвестная категория анкеты.", reply_markup=main_menu_kb()
            )
            return
        ctx.user_data[S_MODE]      = "quiz"
        ctx.user_data[S_QUIZ_KIND] = kind
        ctx.user_data[S_QUIZ_IDX]  = 0
        ctx.user_data[S_QUIZ_ANS]  = []
        await q.edit_message_text(cfg["intro"], parse_mode=ParseMode.MARKDOWN)
        await ctx.bot.send_message(
            q.message.chat_id,
            f"*Вопрос 1 из {cfg['total']}:*\n\n{cfg['questions'][0]}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=yes_no_kb(),
        )
        return

    if data.startswith("q:"):
        await handle_quiz_answer(update, ctx, data == "q:yes")
        return

    if data == "book":
        ctx.user_data[S_MODE] = "lead"
        await q.edit_message_text(LEAD_PROMPT, parse_mode=ParseMode.MARKDOWN)
        return

    if data == "pricing":
        ctx.user_data[S_MODE] = None
        await q.edit_message_text(
            PRICING_TEXT,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📞 Записаться на консультацию", callback_data="book")],
                [InlineKeyboardButton("⬅️ В меню",                    callback_data="menu")],
            ]),
        )
        return

    if data == "case_review":
        ctx.user_data[S_MODE] = "case_review"
        ctx.user_data["case_review_started"] = False
        await q.edit_message_text(
            "🆓 *Бесплатный разбор вашей ситуации*\n\n"
            "⚠️ *Важно:* всё, что вы здесь напишете и приложите, *пересылается живому специалисту* "
            "— не ИИ-ассистенту. Ответа в боте не будет — эксперт свяжется лично.\n\n"
            "_Если хотите задать вопрос ИИ — нажмите «⬅️ В меню» и выберите «❓ Задать вопрос по визе»._\n\n"
            "Опишите вашу ситуацию (профессия, опыт, цели) и при желании прикрепите документы — "
            "CV, дипломы, статьи, награды, рекомендательные письма.\n\n"
            "📎 *Как прикрепить файл:* нажмите скрепку слева от поля ввода сообщения внизу экрана → "
            "выберите «Файл» или «Фото» → отправьте. Принимаются PDF, DOCX, JPG, PNG и др. "
            "до 2 ГБ за файл.\n\n"
            "Можно отправить *несколькими сообщениями*. Когда закончите — нажмите *«Завершить отправку»*.\n\n"
            "_Специалист свяжется в течение 1-2 рабочих дней._",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=case_review_kb(),
        )
        return

    if data == "case_done":
        if ctx.user_data.get(S_MODE) == "case_review":
            u = q.from_user
            db.save_lead(u.id, u.username, "Бесплатный разбор кейса (см. пересланные сообщения)", "case_review")
            try:
                await safe_send(
                    ctx.bot,
                    ADMIN_CHAT_ID,
                    f"✅ *Завершён сбор материалов* для бесплатного разбора\n\n"
                    f"От: {md_esc(u.first_name)} (@{md_esc(u.username) or '—'}, id `{u.id}`)\n"
                    f"_Все его сообщения и документы пересланы выше._",
                    parse_mode=ParseMode.MARKDOWN,
                )
            except Exception as e:
                log.warning("admin notify failed: %s", e)
            ctx.user_data[S_MODE] = None
            ctx.user_data.pop("case_review_started", None)
            await q.edit_message_text(
                "✅ Спасибо! Эксперт изучит вашу заявку и свяжется с вами в течение "
                "1-2 рабочих дней.",
                reply_markup=main_menu_kb(),
            )
        return

async def handle_quiz_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE, is_yes: bool):
    q = update.callback_query
    kind = ctx.user_data.get(S_QUIZ_KIND)
    idx  = ctx.user_data.get(S_QUIZ_IDX, 0)
    ans  = ctx.user_data.get(S_QUIZ_ANS, [])
    cfg  = quiz.get_quiz(kind)
    if not cfg:
        await q.edit_message_text("Ошибка состояния. /menu")
        return

    ans.append(is_yes)
    idx += 1
    ctx.user_data[S_QUIZ_ANS] = ans
    ctx.user_data[S_QUIZ_IDX] = idx

    if idx < cfg["total"]:
        await q.edit_message_text(
            f"*Вопрос {idx+1} из {cfg['total']}:*\n\n{cfg['questions'][idx]}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=yes_no_kb(),
        )
        return

    verdict, qualifies = quiz.summarize(kind, ans)
    ctx.user_data[S_MODE] = None

    u = q.from_user
    detail = "\n".join(
        f"{'✅' if a else '❌'} {cfg['questions'][i]}"
        for i, a in enumerate(ans)
    )
    admin_txt = (
        f"📋 *Квалификационная анкета завершена*\n\n"
        f"Пользователь: {md_esc(u.first_name)} (@{md_esc(u.username) or '—'}, id {u.id})\n"
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

    await q.edit_message_text(verdict, parse_mode=ParseMode.MARKDOWN, reply_markup=post_quiz_kb())

async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    db.upsert_user(u.id, u.username, u.first_name)
    text = update.message.text.strip()
    mode = ctx.user_data.get(S_MODE)

    if mode == "lead":
        db.save_lead(u.id, u.username, text, "booking")
        ctx.user_data[S_MODE] = None
        admin_txt = (
            f"📞 *Новая заявка на консультацию*\n\n"
            f"От: {md_esc(u.first_name)} (@{md_esc(u.username) or '—'}, id {u.id})\n\n"
            f"{md_esc(text)}"
        )
        try:
            await safe_send(ctx.bot, ADMIN_CHAT_ID, admin_txt, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            log.warning("admin notify failed: %s", e)
        await update.message.reply_text(LEAD_RECEIVED, reply_markup=main_menu_kb())
        return

    if mode == "case_review":
        await _forward_case_review(update, ctx, "text")
        return

    allowed, new_count = db.try_consume_daily(u.id, DAILY_LIMIT)
    if not allowed:
        await update.message.reply_text(
            LIMIT_REACHED,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📞 Записаться на консультацию", callback_data="book")
            ]]),
        )
        return

    await ctx.bot.send_chat_action(update.effective_chat.id, "typing")

    history = db.recent_history(u.id, limit=8)
    try:
        answer, offer_consultation = await llm.ask(history, text)
    except Exception:
        log.exception("LLM error")
        db.save_msg(u.id, "user", text)
        await update.message.reply_text(
            "Временная ошибка при обращении к базе знаний. Попробуйте ещё раз через минуту."
        )
        return

    db.save_msg(u.id, "user", text)
    db.save_msg(u.id, "assistant", answer)

    left = DAILY_LIMIT - new_count
    footer = f"\n\n_Осталось сегодня: {left}/{DAILY_LIMIT}_"

    kb = None
    if offer_consultation:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 Записаться на консультацию",  callback_data="book")],
            [InlineKeyboardButton("🆓 Бесплатный разбор ситуации", callback_data="case_review")],
            [InlineKeyboardButton("⬅️ В меню", callback_data="menu")],
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

    if not ctx.user_data.get("case_review_started"):
        try:
            await safe_send(
                ctx.bot,
                ADMIN_CHAT_ID,
                f"🆓 *Новая заявка на бесплатный разбор*\n\n"
                f"От: {md_esc(u.first_name)} (@{md_esc(u.username) or '—'}, id `{u.id}`)\n"
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
            "✓ Передал специалисту. Он ответит лично (не через бот) в течение "
            "1-2 рабочих дней.\n\n"
            "Можно отправить ещё материалы или нажать «Завершить отправку».",
            reply_markup=case_review_kb(),
        )
    else:
        await update.message.reply_text(
            "⚠️ Не удалось передать это сообщение специалисту. "
            "Попробуйте ещё раз или напишите текстом в «Записаться на консультацию».",
            reply_markup=case_review_kb(),
        )

async def _forward_booking_attachment(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Forward attachment sent during lead (booking) mode to the admin."""
    u = update.effective_user
    db.upsert_user(u.id, u.username, u.first_name)
    db.save_lead(u.id, u.username, "Файл приложен к заявке (см. пересланное сообщение)", "booking_file")
    try:
        await safe_send(
            ctx.bot,
            ADMIN_CHAT_ID,
            f"📎 *Файл к заявке на консультацию*\n\n"
            f"От: {md_esc(u.first_name)} (@{md_esc(u.username) or '—'}, id `{u.id}`)\n"
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
        await update.message.reply_text(
            "✓ Файл получен. Если ещё не прислали имя и описание — пришлите одним сообщением."
        )
    else:
        await update.message.reply_text(
            "⚠️ Не удалось передать файл специалисту. Попробуйте ещё раз "
            "или опишите ситуацию текстом."
        )

async def on_attachment(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle non-text messages (documents/photos/voice/video/audio)."""
    mode = ctx.user_data.get(S_MODE)
    if mode == "case_review":
        await _forward_case_review(update, ctx, "attachment")
        return
    if mode == "lead":
        await _forward_booking_attachment(update, ctx)
        return
    await update.message.reply_text(
        "Чтобы отправить документы — выберите в меню «🆓 Бесплатный разбор ситуации» "
        "или «📞 Записаться на консультацию».",
        reply_markup=main_menu_kb(),
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
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("menu",  cmd_menu))
    app.add_handler(CommandHandler("reset", cmd_reset))
    app.add_handler(CommandHandler("users", cmd_users))
    app.add_handler(CommandHandler("chat",  cmd_chat))
    app.add_handler(CommandHandler("leads", cmd_leads))
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
