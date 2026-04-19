# Telegram Bot — US Visa Assistant (EB-1A / EB-2 NIW / O-1)

ИИ-ассистент на базе Claude Sonnet 4.6. Отвечает на вопросы по трём визовым категориям на русском, на основе правил USCIS (8 CFR, INA, AAO, *Kazarian*, *Matter of Dhanasar*).

## Возможности

- Q&A с ограничением 10 сообщений/день на пользователя
- Квалификационная анкета (Да/Нет) для EB-1A (10 критериев), EB-2 NIW (3-prong Dhanasar), O-1 (8 критериев)
- Запись на консультацию → уведомление админу
- «Связаться со специалистом» → уведомление админу
- Вне специализации (H-1B, L-1, family-based) — автоматически предлагает передать живому человеку
- SQLite хранит пользователей, счётчики, лиды и историю диалогов

## Локальный запуск

```bash
cd tg_bot
python3 -m pip install -r requirements.txt
cp .env.example .env
# Заполнить .env: TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, ADMIN_CHAT_ID
python3 bot.py
```

### Как получить значения для .env

- **TELEGRAM_BOT_TOKEN** — @BotFather в Telegram → `/newbot` → получите токен.
- **ANTHROPIC_API_KEY** — https://console.anthropic.com/settings/keys.
- **ADMIN_CHAT_ID** — напишите `@userinfobot` в Telegram, он ответит вашим ID.

## Деплой на Railway (рекомендуется)

1. Создать репозиторий на GitHub, запушить папку `tg_bot/`.
2. Зарегистрироваться на https://railway.app (Login with GitHub).
3. **New Project → Deploy from GitHub repo** → выбрать репозиторий.
4. Railway автоматически определит Python, установит `requirements.txt` и запустит `Procfile`.
5. **Variables** → добавить:
   - `TELEGRAM_BOT_TOKEN`
   - `ANTHROPIC_API_KEY`
   - `ADMIN_CHAT_ID`
6. **Settings → Networking** → для worker процесса ничего не требуется (бот работает через long polling, а не webhook).
7. Деплой готов. Логи — вкладка **Deployments → View Logs**.

Бесплатный лимит Railway: $5/месяц execution credit — для одиночного бота хватит с запасом.

## Альтернативы хостинга

- **Fly.io** — $0 free tier, сложнее конфиг.
- **VPS Hetzner CX11** — €4.5/мес, полный контроль, нужен systemd unit.
- **Render** — free tier, но инстанс засыпает через 15 мин бездействия (не подходит для бота).
- **Локальный компьютер** — бесплатно, но компьютер должен быть постоянно включён.

## Команды бота

- `/start` — дисклеймер + главное меню
- `/menu` — показать главное меню
- `/reset` — сбросить контекст диалога

## Структура

```
tg_bot/
├── bot.py           # Хендлеры, меню, квиз, лиды
├── llm.py           # Обёртка Anthropic API с prompt caching
├── db.py            # SQLite: users, daily_count, leads, history
├── prompts.py       # Системный промпт, дисклеймер, тексты
├── quiz.py          # Логика квалификационной анкеты
├── requirements.txt
├── Procfile         # Для Railway
├── .env.example     # Шаблон переменных окружения
└── README.md
```

## Настройка

- **Изменить дневной лимит**: `bot.py` → `DAILY_LIMIT = 10`
- **Сменить модель**: `llm.py` → `MODEL = "claude-sonnet-4-6"` (варианты: `claude-opus-4-7`, `claude-haiku-4-5-20251001`)
- **Изменить системный промпт**: `prompts.py` → `SYSTEM_PROMPT`
- **Добавить вопросы в анкету**: `prompts.py` → `EB1A_QUESTIONS` / `NIW_QUESTIONS` / `O1_QUESTIONS`
