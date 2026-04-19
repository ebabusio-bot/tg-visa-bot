# -*- coding: utf-8 -*-
"""Telegram bot: US immigration assistant for EB-1A / EB-2 NIW / O-1."""
import logging
import os
from dotenv import load_dotenv

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters,
)

import db
import llm
import quiz
from prompts import (
    DISCLAIMER, WELCOME, LIMIT_REACHED,
    LEAD_PROMPT, LEAD_RECEIVED, QUIZ_START,
)

load_dotenv()

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ADMIN_CHAT_ID = int(os.environ["ADMIN_CHAT_ID"])
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

def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("❓ Задать вопрос по визе",         callback_data="ask")],
        [InlineKeyboardButton("📋 Оценить шансы (анкета)",       callback_data="quiz")],
        [InlineKeyboardButton("🆓 Бесплатный разбор ситуации",   callback_data="case_review")],
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
        [InlineKeyboardButton("❓ Задать уточняющий вопрос",   callback_data="ask")],
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
    return update.effective_user and update.effective_user.id == ADMIN_CHAT_ID

async def cmd_users(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return
    rows = db.list_users_with_stats(limit=50)
    if not rows:
        await update.message.reply_text("Пользователей пока нет.")
        return
    lines = ["*Пользователи бота* (последние 50):\n"]
    for r in rows:
        name = r["first_name"] or "—"
        uname = f"@{r['username']}" if r["username"] else "—"
        last = (r["last_msg"] or "—")[:16]
        lines.append(
            f"`{r['tg_id']}` · {name} · {uname}\n"
            f"   сообщений: {r['msg_count']} · последнее: {last}"
        )
    lines.append("\n_Чтобы посмотреть переписку:_ `/chat <id>`")
    await update.message.reply_text(
        "\n".join(lines), parse_mode=ParseMode.MARKDOWN
    )

async def cmd_chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return
    if not ctx.args:
        await update.message.reply_text(
            "Использование: `/chat <tg_id>`\nID берите из `/users`.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return
    try:
        tg_id = int(ctx.args[0])
    except ValueError:
        await update.message.reply_text("ID должен быть числом.")
        return
    msgs = db.full_history(tg_id, limit=100)
    if not msgs:
        await update.message.reply_text(f"С пользователем `{tg_id}` переписки нет.",
                                        parse_mode=ParseMode.MARKDOWN)
        return
    chunks: list[str] = [f"*Переписка с `{tg_id}`* (до 100 сообщ.):\n"]
    for m in msgs:
        who = "👤" if m["role"] == "user" else "🤖"
        ts = (m["created_at"] or "")[:16]
        body = (m["content"] or "").replace("`", "'")
        chunks.append(f"{who} _{ts}_\n{body}\n")
    text = "\n".join(chunks)
    for i in range(0, len(text), 3500):
        await update.message.reply_text(text[i:i + 3500], parse_mode=ParseMode.MARKDOWN)

async def cmd_leads(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return
    rows = db.list_leads(limit=30)
    if not rows:
        await update.message.reply_text("Заявок пока нет.")
        return
    lines = ["*Последние заявки* (до 30):\n"]
    for r in rows:
        ts = (r["created_at"] or "")[:16]
        uname = f"@{r['username']}" if r["username"] else "—"
        src = r["source"] or "—"
        payload = (r["payload"] or "")[:200]
        lines.append(
            f"_{ts}_ · {src} · {uname} · `{r['tg_id']}`\n{payload}\n"
        )
    text = "\n".join(lines)
    for i in range(0, len(text), 3500):
        await update.message.reply_text(text[i:i + 3500], parse_mode=ParseMode.MARKDOWN)

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
            "Задайте ваш вопрос по EB-1A, EB-2 NIW или O-1. "
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

    if data == "case_review":
        ctx.user_data[S_MODE] = "case_review"
        ctx.user_data["case_review_started"] = False
        await q.edit_message_text(
            "🆓 *Бесплатный разбор вашей ситуации*\n\n"
            "Опишите вашу ситуацию (профессия, опыт, цели) и при желании прикрепите документы — "
            "CV, дипломы, статьи, награды, рекомендательные письма.\n\n"
            "📎 *Как прикрепить файл:* нажмите скрепку слева от поля ввода сообщения внизу экрана → "
            "выберите «Файл» или «Фото» → отправьте. Принимаются PDF, DOCX, JPG, PNG и др. "
            "до 2 ГБ за файл.\n\n"
            "Можно отправить *несколькими сообщениями* — я всё передам специалисту. "
            "Когда закончите — нажмите *«Завершить отправку»*.\n\n"
            "_Эксперт изучит вашу ситуацию и свяжется лично в течение 1-2 рабочих дней._",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=case_review_kb(),
        )
        return

    if data == "case_done":
        if ctx.user_data.get(S_MODE) == "case_review":
            u = q.from_user
            db.save_lead(u.id, u.username, "Бесплатный разбор кейса (см. пересланные сообщения)", "case_review")
            try:
                await ctx.bot.send_message(
                    ADMIN_CHAT_ID,
                    f"✅ *Завершён сбор материалов* для бесплатного разбора\n\n"
                    f"От: {u.first_name or ''} (@{u.username or '—'}, id `{u.id}`)\n"
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
        f"Пользователь: {u.first_name or ''} (@{u.username or '—'}, id {u.id})\n"
        f"Виза: *{kind.upper()}*\n"
        f"Результат: {sum(ans)}/{cfg['total']} — "
        f"{'✅ квалифицируется' if qualifies else '⚠️ под вопросом'}\n\n"
        f"{detail}"
    )
    try:
        await ctx.bot.send_message(ADMIN_CHAT_ID, admin_txt, parse_mode=ParseMode.MARKDOWN)
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
            f"От: {u.first_name or ''} (@{u.username or '—'}, id {u.id})\n\n"
            f"{text}"
        )
        try:
            await ctx.bot.send_message(ADMIN_CHAT_ID, admin_txt, parse_mode=ParseMode.MARKDOWN)
        except Exception as e:
            log.warning("admin notify failed: %s", e)
        await update.message.reply_text(LEAD_RECEIVED, reply_markup=main_menu_kb())
        return

    if mode == "case_review":
        await _forward_case_review(update, ctx, "text")
        return

    count = db.get_today_count(u.id)
    if count >= DAILY_LIMIT:
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
        await update.message.reply_text(
            "Временная ошибка при обращении к базе знаний. Попробуйте ещё раз через минуту."
        )
        return

    db.inc_today_count(u.id)
    db.save_msg(u.id, "user", text)
    db.save_msg(u.id, "assistant", answer)

    left = DAILY_LIMIT - (count + 1)
    footer = f"\n\n_Осталось сегодня: {left}/{DAILY_LIMIT}_"

    if offer_consultation:
        kb = InlineKeyboardMarkup([
            [InlineKeyboardButton("📞 Записаться на консультацию",  callback_data="book")],
            [InlineKeyboardButton("🆓 Бесплатный разбор ситуации", callback_data="case_review")],
            [InlineKeyboardButton("⬅️ В меню", callback_data="menu")],
        ])
        await update.message.reply_text(
            answer + footer, parse_mode=ParseMode.MARKDOWN, reply_markup=kb
        )
    else:
        await update.message.reply_text(answer + footer, parse_mode=ParseMode.MARKDOWN)

async def _forward_case_review(update: Update, ctx: ContextTypes.DEFAULT_TYPE, kind: str):
    """Forward a user's text/document/photo to the admin during case_review mode."""
    u = update.effective_user
    db.upsert_user(u.id, u.username, u.first_name)

    if not ctx.user_data.get("case_review_started"):
        try:
            await ctx.bot.send_message(
                ADMIN_CHAT_ID,
                f"🆓 *Новая заявка на бесплатный разбор*\n\n"
                f"От: {u.first_name or ''} (@{u.username or '—'}, id `{u.id}`)\n"
                f"_Ниже пересылаются его сообщения и документы:_",
                parse_mode=ParseMode.MARKDOWN,
            )
        except Exception as e:
            log.warning("admin notify failed: %s", e)
        ctx.user_data["case_review_started"] = True

    try:
        await ctx.bot.forward_message(
            chat_id=ADMIN_CHAT_ID,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
        )
    except Exception as e:
        log.warning("forward failed: %s", e)

    await update.message.reply_text(
        "✓ Получено. Отправьте ещё материалы или нажмите *«Завершить отправку»*.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=case_review_kb(),
    )

async def on_attachment(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Handle documents/photos — only meaningful inside case_review mode."""
    if ctx.user_data.get(S_MODE) != "case_review":
        await update.message.reply_text(
            "Чтобы отправить документы — выберите в меню «🆓 Бесплатный разбор ситуации».",
            reply_markup=main_menu_kb(),
        )
        return
    await _forward_case_review(update, ctx, "attachment")

async def on_error(update: object, ctx: ContextTypes.DEFAULT_TYPE):
    log.exception("Update error", exc_info=ctx.error)

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
    app.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO, on_attachment))
    app.add_error_handler(on_error)
    log.info("Bot started. Model=%s, daily_limit=%d", llm.MODEL, DAILY_LIMIT)
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
