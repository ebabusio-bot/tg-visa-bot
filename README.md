# Telegram Bot — US Visa Assistant (EB-1A / EB-2 NIW / EB-3 / O-1 / E-2 + asylum)

ИИ-ассистент на базе Claude (`claude-sonnet-4-6`). Отвечает на вопросы по визовым
категориям США на нескольких языках, на основе правил USCIS (8 CFR, INA, AAO,
*Kazarian*, *Matter of Dhanasar*). Один и тот же код можно продавать разным
фирмам (white-label) — настройка только через `.env`, без правки кода.

## Возможности

- Q&A с ограничением вопросов на пользователя (`QUESTION_LIMIT`, по умолч. 25)
- Квалификационные анкеты (Да/Нет): EB-1A, EB-2 NIW, EB-3, O-1, E-2
- Бесплатный чеклист документов по выбранной категории
- Живой хэндофф: «Записаться» / «Связаться с человеком» → лид админу,
  ответы клиенту уходят от бота (`/reply <id> <текст>`)
- Дублирование лидов в WhatsApp второму администратору (CallMeBot, опционально)
- Ежедневный мониторинг официальных источников (Federal Register API + Visa
  Bulletin) с алертами об изменениях правил/пошлин
- Многоязычность: ru / uk / en / es (расширяемо), выбор и переключение языка
- Учёт расходов на ИИ и месячный бюджет (`/costs`)
- SQLite: пользователи, счётчики, лиды, история диалогов, события, снапшоты мониторинга

## Локальный запуск

```bash
cd tg_bot
python3 -m pip install -r requirements.txt
cp .env.example .env
# Заполнить .env: как минимум TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY, ADMIN_CHAT_ID
python3 bot.py
```

### Как получить значения для .env

- **TELEGRAM_BOT_TOKEN** — @BotFather в Telegram → `/newbot` → токен.
- **ANTHROPIC_API_KEY** — https://console.anthropic.com/settings/keys.
- **ADMIN_CHAT_ID** — напишите `@userinfobot`, он ответит вашим ID.

См. полный список переменных и их описание в [.env.example](.env.example).

## Деплой (Hetzner VPS, systemd) — РУЧНОЙ

Бот работает на Hetzner CX-сервере под `systemd` (не Railway, не авто-деплой).
`git push` **сам по себе НЕ обновляет код на сервере** — нужно залить файлы и
перезапустить службу вручную.

**Первичная установка** (один раз, на свежем Ubuntu 24.04, под root):

1. Залить файлы в `/home/bot/tg_bot/` через `scp`.
2. Создать `/home/bot/tg_bot/.env` (см. `.env.example`).
3. `bash deploy_hetzner.sh` — поставит venv, создаст службы `tgbot` и
   `healthcheck`, запустит их.

**Обновление кода** (каждый раз после изменений):

```bash
# с локальной машины — заливаем ТОЛЬКО код, НЕ базу и НЕ .env:
scp *.py bot@SERVER:/home/bot/tg_bot/
# на сервере:
ssh bot@SERVER 'sudo systemctl restart tgbot'
```

> ⚠️ **Никогда не заливайте `bot.db` и `.env` поверх сервера** — затрёте живую
> базу (пользователи, лиды, история) и рабочие ключи. Оба файла в `.gitignore`,
> поэтому в репозиторий они не попадают. Бэкап базы на сервере:
> `cp /home/bot/tg_bot/bot.db ~/bot.db.$(date +%F)`.

Логи: `journalctl -u tgbot -f`. Здоровье: `healthcheck.py` отдаёт 200/503 для
внешнего мониторинга (UptimeRobot), не падает при рестартах бота.

## White-label: продажа клонов фирмам

Один код → разные фирмы, всё через `.env` (без форка):

| Переменная | Назначение |
|---|---|
| `FIRM_NAME` | Название фирмы: строка в приветствии + тег в техно-алертах |
| `BOT_LANGS` | Какие языки предлагать, напр. `en,es` (пусто = все) |
| `DEFAULT_LANG` | Язык по умолчанию (должен быть среди `BOT_LANGS`) |
| `ADMIN_CHAT_ID` | Чат(ы) КЛИЕНТА для лидов/заявок (можно несколько через запятую) |
| `OWNER_CHAT_ID` | ВАШ чат для техно-алертов (ошибки/сбои); пусто = идут на ADMIN |
| `PRICE_CONSULT` / `PRICE_PETITION` / `PRICE_I485_MEMBER` | Цены УСЛУГ фирмы (госпошлины USCIS не настраиваются — это факты) |
| `AI_BUDGET_USD` | Месячный бюджет на ИИ для `/costs` (0 = выключено) |
| `WHATSAPP_NOTIFY_PHONE` / `CALLMEBOT_APIKEY` | Дубль лидов в WhatsApp (опц.) |

У каждого клона — своя папка, свой `.env`, своя `bot.db`. Проверка настройки:
`/whoami` (показывает фирму, ADMIN/OWNER) и `/testnotify` (шлёт тест в оба канала).

## Команды бота

Пользовательские: `/start`, `/menu`, `/reset`, `/lang`.

Админские (только для `ADMIN_CHAT_ID`):
`/whoami`, `/testnotify`, `/testwa`, `/users`, `/chat`, `/leads`, `/stats`,
`/costs`, `/reply <id> <текст>`, `/checkupdates`, `/sources`.

## Структура

```
tg_bot/
├── bot.py          # Хендлеры, меню, квиз, лиды, фоновые джобы
├── config.py       # White-label конфиг из .env (FIRM_NAME, цены)
├── llm.py          # Обёртка Anthropic API с prompt caching + учёт расходов
├── db.py           # SQLite-слой
├── i18n.py         # Многоязычные тексты UI + рендер приветствия/цен
├── prompts.py      # Системный промпт, дисклеймер, тексты
├── quiz.py         # Логика квалификационных анкет
├── monitor.py      # Мониторинг Federal Register + Visa Bulletin
├── whatsapp.py     # CallMeBot-уведомления (опц.)
├── healthcheck.py  # Отдельная служба healthcheck для UptimeRobot
├── deploy_hetzner.sh
├── requirements.txt
├── .env.example
└── README.md
```

## Настройка кода

- **Дневной лимит вопросов**: `bot.py` → `QUESTION_LIMIT`
- **Модель**: `llm.py` → `MODEL` (`claude-sonnet-4-6`)
- **Системный промпт**: `prompts.py` → `SYSTEM_PROMPT`
- **Вопросы анкет**: `prompts.py` / `quiz.py`
- **Тексты UI и языки**: `i18n.py`
