# -*- coding: utf-8 -*-
"""Multi-language UI strings. Admin-facing text stays Russian in bot.py."""

import os

# All languages this codebase has translations for. A single deployment can
# expose a subset via the BOT_LANGS env var, so the same code can run as a
# RU/UK/EN/ES bot and, separately, as an EN/ES-only bot — no code fork.
# (code, flag, native_name)
_ALL_LANGUAGES: list[tuple[str, str, str]] = [
    ("en", "🇬🇧", "English"),
    ("es", "🇪🇸", "Español"),
    ("ru", "🇷🇺", "Русский"),
    ("uk", "🇺🇦", "Українська"),
]

# BOT_LANGS, e.g. "en,es" — restrict which languages this instance offers.
# Unset/empty → all of the above (current default behaviour).
_enabled = [c.strip() for c in os.environ.get("BOT_LANGS", "").replace(";", ",").split(",") if c.strip()]
LANGUAGES: list[tuple[str, str, str]] = (
    [row for row in _ALL_LANGUAGES if row[0] in _enabled] or _ALL_LANGUAGES
)

LANG_CODES = {c for c, _, _ in LANGUAGES}

# DEFAULT_LANG env, e.g. "en". Must be one of the enabled languages, otherwise
# we fall back to the first enabled one.
DEFAULT_LANG = (os.environ.get("DEFAULT_LANG", "ru").strip() or "ru")
if DEFAULT_LANG not in LANG_CODES:
    DEFAULT_LANG = LANGUAGES[0][0]

# For admin-facing text (Russian).
LANG_NAMES_RU: dict[str, str] = {
    "ru": "русский",
    "uk": "украинский",
    "en": "английский",
    "es": "испанский",
}

LANG_FLAGS: dict[str, str] = {c: f for c, f, _ in LANGUAGES}

# For each language, the native name of that language (used in the LLM
# language directive, e.g. "respond in Español").
LANG_NATIVE: dict[str, str] = {c: n for c, _, n in LANGUAGES}

# Multilingual initial language prompt (shown before any greeting, in every
# ENABLED language at once so the user can recognise their own).
_PICKER_PHRASES: dict[str, str] = {
    "en": "Please choose your language",
    "es": "Por favor, elija su idioma",
    "ru": "Пожалуйста, выберите язык",
    "uk": "Будь ласка, оберіть мову",
}
LANGUAGE_PICKER_PROMPT = "🌐 " + " · ".join(
    _PICKER_PHRASES.get(c, c) for c, _, _ in LANGUAGES
)


# Full string dictionary. Each language has the same set of keys.
# Fallback: if a key is missing for a language, falls back to English.
T: dict[str, dict[str, object]] = {

    # ────────────────────────────────────────────────────────────────── ru
    "ru": {
        "welcome": (
            "Здравствуйте! 🇺🇸\n"
            "Я — ИИ-помощник по визам США. Основные категории: *EB-1A*, *EB-2 NIW*, *EB-3*, *O-1*, *E-2*. "
            "Также отвечаю на справочные вопросы по *убежищу (asylum)*. Помогу разобраться:\n"
            "• в критериях квалификации\n"
            "• в требованиях к документам\n"
            "• в типовых причинах отказов и стратегиях\n\n"
            "Расскажите о своей ситуации или задайте конкретный вопрос.\n\n"
            "⚠️ Представленная информация носит справочный характер "
            "и не является юридической консультацией. "
            "Каждый случай уникален и требует индивидуального рассмотрения."
        ),
        "language_saved": "✅ Язык установлен: *Русский*",
        "menu_header": "Главное меню:",
        "context_reset": "Контекст сброшен. Выберите действие:",
        "lang_changed": "Выберите язык:",

        "btn_ask": "❓ Задать вопрос по визе",
        "btn_quiz": "📋 Оценить шансы (анкета)",
        "btn_case_review": "🆓 Бесплатный разбор ситуации",
        "btn_pricing": "💰 Стоимость и сроки",
        "btn_book": "📞 Записаться на консультацию",
        "btn_contact_human": "👤 Связаться с человеком",
        "human_prompt": (
            "✍️ Опишите ваш вопрос одним сообщением — я передам его нашему "
            "специалисту, и он ответит вам прямо здесь, в этом чате."
        ),
        "human_relayed": (
            "✅ Сообщение передано специалисту. Он ответит вам здесь — можете "
            "написать ещё или прислать документы."
        ),
        "btn_back": "⬅️ В меню",
        "btn_checklist": "🎁 Бесплатный чеклист документов",
        "checklist_select": (
            "🎁 *Бесплатный чеклист документов для петиции.*\n\nВыберите визу:"
        ),
        "checklist_contact_prompt": (
            "📋 Отлично! Напишите одним сообщением ваше *имя* и *email или телефон* — "
            "наши специалисты пришлют чеклист и при необходимости ответят на вопросы."
        ),
        "checklist_sent": (
            "✅ Спасибо! Ваш чеклист — ниже. Наши специалисты также свяжутся с вами."
        ),
        "btn_support": "🛠 Техподдержка",
        "support_info": (
            "🛠 *Техподдержка*\n\n"
            "Напишите следующим сообщением ваш вопрос или проблему с работой бота — "
            "оно будет передано в поддержку. Можно приложить скриншот."
        ),
        "support_sent": (
            "✅ Ваше сообщение передано в техподдержку. "
            "Мы свяжемся с вами в ближайшее время."
        ),
        "support_failed": (
            "⚠️ Не удалось передать сообщение. Попробуйте ещё раз позже."
        ),
        "btn_reminder_resume": "📋 Доделать квиз",
        "reminder_quiz_incomplete": (
            "👋 Вы начали оценку шансов по *{kind}*, но не завершили её. "
            "Хотите доделать сейчас?"
        ),
        "reminder_reengagement": (
            "👋 Вчера вы заходили к ИИ-ассистенту по иммиграции в США. "
            "Могу ли я ответить на ваши вопросы? "
            "Могу также предложить Вам записаться на консультацию."
        ),
        "reminder_lead_followup": (
            "👋 Здравствуйте! Недавно вы оставили заявку — наши специалисты "
            "готовы разобрать вашу ситуацию. Подскажите, как вам удобнее: "
            "звонок или переписка? Если появились новые вопросы — задайте их здесь."
        ),
        "btn_case_done": "✅ Завершить отправку",
        "btn_yes": "✅ Да",
        "btn_no": "❌ Нет",
        "btn_lang": "🌐 Сменить язык",

        "btn_quiz_eb1a": "EB-1A (Extraordinary Ability)",
        "btn_quiz_niw":  "EB-2 NIW (National Interest)",
        "btn_quiz_o1":   "O-1 (Extraordinary Ability)",
        "btn_quiz_e2":   "E-2 (Treaty Investor)",

        "ask_prompt": (
            "Задайте ваш вопрос по EB-1A, EB-2 NIW, O-1, E-2 или убежищу. "
            "Отвечаю на основе правил USCIS.\n\n"
            "ℹ️ Можно задать до {total} вопросов. "
            "Когда лимит закончится, предложим записаться на консультацию со специалистом.\n\n"
            "_Осталось вопросов: {left}/{total}_"
        ),
        "quiz_start": "Оценка шансов по критериям USCIS.\n\nПо какой визе хотите пройти анкету?",
        "quiz_q_header": "*Вопрос {n} из {total}:*\n\n{q}",
        "quiz_not_active": "Анкета больше не активна. Выберите действие:",
        "in_quiz_warning": (
            "Вы сейчас проходите анкету — отвечайте кнопками *«✅ Да»* или *«❌ Нет»* "
            "под вопросом выше. Если хотите выйти из анкеты — /menu."
        ),
        "unknown_quiz": "Неизвестная категория анкеты.",

        "limit_reached": (
            "Вы достигли лимита в {total} вопросов. "
            "Для продолжения рекомендую связаться с нашими специалистами — они разберут вашу ситуацию индивидуально."
        ),
        "footer_remaining": "\n\n_Осталось вопросов: {left}/{total}_",
        "llm_error": "Временная ошибка при обращении к базе знаний. Попробуйте ещё раз через минуту.",
        "too_many_msgs": "⏳ Слишком много сообщений подряд. Пожалуйста, подождите немного и напишите снова.",

        "lead_prompt": (
            "Чтобы наши специалисты связались с вами, пожалуйста, укажите:\n\n"
            "1️⃣ *Имя*\n"
            "2️⃣ *Коротко о вашей ситуации* (профессия, виза, которая интересует)\n\n"
            "Отправьте одним сообщением."
        ),
        "lead_received": (
            "✅ Спасибо! Ваша заявка принята. "
            "Наши специалисты свяжутся с вами в течение рабочего дня."
        ),

        "case_review_info": (
            "🆓 *Бесплатный разбор вашей ситуации*\n\n"
            "⚠️ *Важно:* всё, что вы здесь напишете и приложите, *пересылается живым специалистам* "
            "— не ИИ-ассистенту. Ответа в боте не будет — наши специалисты свяжутся лично.\n\n"
            "_Если хотите задать вопрос ИИ — нажмите «⬅️ В меню» и выберите «❓ Задать вопрос по визе»._\n\n"
            "Опишите вашу ситуацию (профессия, опыт, цели) и при желании прикрепите документы — "
            "CV, дипломы, статьи, награды, рекомендательные письма.\n\n"
            "📎 *Как прикрепить файл:* нажмите скрепку слева от поля ввода сообщения внизу экрана → "
            "выберите «Файл» или «Фото» → отправьте. Принимаются PDF, DOCX, JPG, PNG и др. "
            "до 2 ГБ за файл.\n\n"
            "Можно отправить *несколькими сообщениями*. Когда закончите — нажмите *«Завершить отправку»*.\n\n"
            "_Наши специалисты свяжутся в течение 1-2 рабочих дней._"
        ),
        "case_review_forwarded": (
            "✓ Передал нашим специалистам. Они ответят лично (не через бот) в течение "
            "1-2 рабочих дней.\n\n"
            "Можно отправить ещё материалы или нажать «Завершить отправку»."
        ),
        "case_review_forward_failed": (
            "⚠️ Не удалось передать это сообщение нашим специалистам. "
            "Попробуйте ещё раз или напишите текстом в «Записаться на консультацию»."
        ),
        "case_review_done": (
            "✅ Спасибо! Наши специалисты изучат вашу заявку и свяжутся с вами в течение "
            "1-2 рабочих дней."
        ),
        "case_button_inactive": "Эта кнопка уже не активна. Выберите действие:",
        "booking_file_ok": "✓ Файл получен. Если ещё не прислали имя и описание — пришлите одним сообщением.",
        "booking_file_failed": (
            "⚠️ Не удалось передать файл нашим специалистам. Попробуйте ещё раз "
            "или опишите ситуацию текстом."
        ),
        "attachment_hint": (
            "Чтобы отправить документы — выберите в меню «🆓 Бесплатный разбор ситуации» "
            "или «📞 Записаться на консультацию»."
        ),

        "quiz_intro_eb1a": (
            "*EB-1A* — Extraordinary Ability. Нужно соответствовать минимум *3 из 10* критериев "
            "+ положительный Final Merits анализ.\n\nОтвечайте «Да» или «Нет»."
        ),
        "quiz_intro_niw": (
            "*EB-2 NIW* — National Interest Waiver. Тест из дела *Matter of Dhanasar* (2016) — "
            "три обязательных элемента.\n\nОтвечайте «Да» или «Нет»."
        ),
        "quiz_intro_o1": (
            "*O-1A* — виза для людей с выдающимися способностями (наука, бизнес, спорт). "
            "Нужно минимум *3 из 8* критериев.\n\nОтвечайте «Да» или «Нет»."
        ),
        "quiz_intro_e2": (
            "*E-2* — виза для инвесторов из стран с торговым договором с США.\n\n"
            "🌍 *Страны бывшего СССР и E-2:*\n"
            "✅ *Подпадают*: Украина, Грузия, Армения, Азербайджан, "
            "Казахстан, Кыргызстан, Молдова, Эстония, Латвия, Литва.\n"
            "❌ *НЕ подпадают*: *Россия*, *Беларусь*, *Узбекистан*, *Таджикистан*, *Туркменистан*.\n\n"
            "В отличие от EB-категорий, *все 7 требований E-2 обязательны*.\n\n"
            "Отвечайте «Да» или «Нет»."
        ),

        "eb1a_questions": [
            "🏆 У вас есть крупные национальные или международные награды/премии (кроме Нобелевской и подобных)?",
            "👥 Вы состоите в ассоциации, членство в которой требует выдающихся достижений (по мнению признанных экспертов)?",
            "📰 О вас публиковались материалы в крупных профессиональных или общих СМИ?",
            "⚖️ Вы выступали судьёй/рецензентом работ других специалистов в своей области (жюри, peer review и т.п.)?",
            "🔬 Есть ли у вас оригинальный вклад значительной важности в своей области (изобретения, методики, публикации с цитированием)?",
            "📚 Вы автор научных статей в рецензируемых журналах или крупных изданиях?",
            "🎨 Ваши работы выставлялись на художественных выставках или показах?",
            "💼 Вы занимали ведущую или критически важную роль в известной организации?",
            "💰 Ваша зарплата/гонорар существенно выше средней в вашей области?",
            "🎭 У вас есть коммерческий успех в исполнительских искусствах (кассовые сборы, тиражи и т.п.)?",
        ],
        "niw_questions": [
            "🇺🇸 Ваша деятельность имеет существенную важность и национальное значение для США (здравоохранение, технологии, экономика, культура, оборона и т.п.)?",
            "🎯 Вы хорошо подготовлены продвигать эту деятельность (образование, опыт, прогресс, планы, ресурсы, интерес со стороны инвесторов/работодателей)?",
            "⚖️ Есть ли причины, по которым требование PERM labor certification нецелесообразно (срочность, уникальность, ваш вклад перевешивает процедуру)?",
        ],
        "o1_questions": [
            "🏆 У вас есть крупные национальные/международные награды в вашей области?",
            "👥 Членство в ассоциациях, требующих выдающихся достижений?",
            "📰 Публикации о вас в профессиональных или крупных СМИ?",
            "🎯 Оригинальный вклад в область (научный, бизнес, спортивный) значительной важности?",
            "⚖️ Вы выступали судьёй/экспертом работ других специалистов?",
            "📚 Авторство научных статей в своей области?",
            "💼 Работа в критической/важной роли в известных организациях?",
            "💰 Высокая зарплата/гонорар по сравнению с коллегами?",
        ],
        "e2_questions": [
            "🌍 Вы — гражданин страны, имеющей торговый договор (E-2 treaty) с США (например, Украина, Грузия, Армения, Казахстан, Турция; *Россия — нет*, Беларусь — нет)?",
            "💵 Вы уже вложили средства в бизнес в США или они необратимо закоммичены (переведены, контракты подписаны, оборудование куплено)? Средства должны быть «at-risk».",
            "📊 Размер инвестиции существенный и пропорционален стоимости/типу бизнеса (для малого бизнеса обычно от $100–150K+, но зависит от сферы)?",
            "🏢 Это реальный действующий бизнес, производящий товары или услуги (не пассивное владение недвижимостью или ценными бумагами)?",
            "👔 Вы владеете минимум 50% бизнеса или имеете оперативный контроль (сможете «develop and direct» предприятие)?",
            "📈 Бизнес не marginal — то есть приносит или способен принести доход больше минимального для проживания инвестора и/или создаёт рабочие места/вклад в экономику США?",
            "✈️ Вы готовы декларировать намерение выехать из США по окончании статуса E-2 (nonimmigrant intent)?",
        ],

        "pricing": (
            "💰 *Стоимость услуг и сроки*\n\n"
            "*1. Консультация*\n"
            "${consult} (60–90 мин) — разбор по критериям и стратегия по вашей категории. "
            "Входит в стоимость кейса, если далее работаете с нами.\n\n"
            "*2. Юридические услуги (сопровождение петиции командой адвоката)*\n"
            "• *EB-1 (A, C)* или *EB-2 NIW*: *${petition}* — legal service / attorney fees "
            "за оценку и подготовку петиции I-140 + evidence.\n"
            "• *I-485* (подача на грин-карту, когда очередь доступна): "
            "*${member} за каждого члена семьи*.\n"
            "• Платежи прописываются в договоре — обычно 2–3 транша.\n\n"
            "*3. Госпошлины USCIS*\n"
            "• *I-140*: *$715*\n"
            "• Asylum program fee: *$300*\n"
            "• *I-485*: *$1 440*\n"
            "• *Premium Processing*: *$2 805*\n\n"
            "*4. Сроки*\n"
            "• I-140 — около *12–16 месяцев* в стандартном режиме.\n\n"
            "_Актуальные пошлины и сроки сверяйте на uscis.gov._"
        ),
    },

    # ────────────────────────────────────────────────────────────────── uk
    "uk": {
        "welcome": (
            "Вітаю! 🇺🇸\n"
            "Я — ШІ-помічник з американських віз. Основні категорії: *EB-1A*, *EB-2 NIW*, *EB-3*, *O-1*, *E-2*. "
            "Також відповідаю на довідкові питання щодо *притулку (asylum)*. Допоможу розібратися:\n"
            "• з критеріями кваліфікації\n"
            "• з вимогами до документів\n"
            "• з типовими причинами відмов і стратегіями\n\n"
            "Розкажіть про свою ситуацію або поставте конкретне питання.\n\n"
            "⚠️ Наведена інформація має довідковий характер "
            "і не є юридичною консультацією. "
            "Кожен випадок унікальний і потребує індивідуального розгляду."
        ),
        "language_saved": "✅ Мову встановлено: *Українська*",
        "menu_header": "Головне меню:",
        "context_reset": "Контекст скинуто. Оберіть дію:",
        "lang_changed": "Оберіть мову:",

        "btn_ask": "❓ Запитати про візу",
        "btn_quiz": "📋 Оцінити шанси (анкета)",
        "btn_case_review": "🆓 Безкоштовний розбір ситуації",
        "btn_pricing": "💰 Вартість і терміни",
        "btn_book": "📞 Записатися на консультацію",
        "btn_contact_human": "👤 Зв'язатися з фахівцем",
        "human_prompt": (
            "✍️ Опишіть ваше запитання одним повідомленням — я передам його "
            "нашому фахівцю, і він відповість вам просто тут, у цьому чаті."
        ),
        "human_relayed": (
            "✅ Повідомлення передано фахівцю. Він відповість вам тут — можете "
            "написати ще або надіслати документи."
        ),
        "btn_back": "⬅️ До меню",
        "btn_checklist": "🎁 Безкоштовний чеклист документів",
        "checklist_select": (
            "🎁 *Безкоштовний чеклист документів для петиції.*\n\nОберіть візу:"
        ),
        "checklist_contact_prompt": (
            "📋 Чудово! Напишіть одним повідомленням ваше *ім'я* та *email або телефон* — "
            "наші спеціалісти надішлють чеклист і за потреби дадуть відповіді на запитання."
        ),
        "checklist_sent": (
            "✅ Дякуємо! Ваш чеклист — нижче. Наші спеціалісти також зв'яжуться з вами."
        ),
        "btn_support": "🛠 Техпідтримка",
        "support_info": (
            "🛠 *Техпідтримка*\n\n"
            "Напишіть наступним повідомленням ваше запитання або проблему з роботою бота — "
            "воно буде передане в підтримку. Можна додати скриншот."
        ),
        "support_sent": (
            "✅ Ваше повідомлення передано в техпідтримку. "
            "Ми зв'яжемося з вами найближчим часом."
        ),
        "support_failed": (
            "⚠️ Не вдалося передати повідомлення. Спробуйте ще раз пізніше."
        ),
        "btn_reminder_resume": "📋 Завершити анкету",
        "reminder_quiz_incomplete": (
            "👋 Ви розпочали оцінку шансів за *{kind}*, але не завершили її. "
            "Хочете завершити зараз?"
        ),
        "reminder_reengagement": (
            "👋 Вчора ви заходили до ШІ-асистента з імміграції до США. "
            "Чи можу я відповісти на ваші запитання? "
            "Також можу запропонувати Вам записатися на консультацію."
        ),
        "reminder_lead_followup": (
            "👋 Вітаємо! Нещодавно ви залишили заявку — наші спеціалісти "
            "готові розібрати вашу ситуацію. Підкажіть, як вам зручніше: "
            "дзвінок чи листування? Якщо з'явилися нові питання — поставте їх тут."
        ),
        "btn_case_done": "✅ Завершити надсилання",
        "btn_yes": "✅ Так",
        "btn_no": "❌ Ні",
        "btn_lang": "🌐 Змінити мову",

        "btn_quiz_eb1a": "EB-1A (Extraordinary Ability)",
        "btn_quiz_niw":  "EB-2 NIW (National Interest)",
        "btn_quiz_o1":   "O-1 (Extraordinary Ability)",
        "btn_quiz_e2":   "E-2 (Treaty Investor)",

        "ask_prompt": (
            "Поставте своє питання про EB-1A, EB-2 NIW, O-1, E-2 або притулок. "
            "Відповідаю на основі правил USCIS.\n\n"
            "ℹ️ Можна поставити до {total} запитань. "
            "Коли ліміт закінчиться, запропонуємо записатися на консультацію зі спеціалістом.\n\n"
            "_Залишилось запитань: {left}/{total}_"
        ),
        "quiz_start": "Оцінка шансів за критеріями USCIS.\n\nЗа якою візою хочете пройти анкету?",
        "quiz_q_header": "*Питання {n} з {total}:*\n\n{q}",
        "quiz_not_active": "Анкета більше не активна. Оберіть дію:",
        "in_quiz_warning": (
            "Ви зараз проходите анкету — відповідайте кнопками *«✅ Так»* або *«❌ Ні»* "
            "під питанням вище. Щоб вийти з анкети — /menu."
        ),
        "unknown_quiz": "Невідома категорія анкети.",

        "limit_reached": (
            "Ви досягли ліміту у {total} запитань. "
            "Для продовження рекомендую звернутися до фахівця — він розбере вашу ситуацію індивідуально."
        ),
        "footer_remaining": "\n\n_Залишилось запитань: {left}/{total}_",
        "llm_error": "Тимчасова помилка при зверненні до бази знань. Спробуйте ще раз через хвилину.",
        "too_many_msgs": "⏳ Забагато повідомлень поспіль. Будь ласка, зачекайте трохи і напишіть знову.",

        "lead_prompt": (
            "Щоб фахівець зв'язався з вами, будь ласка, вкажіть:\n\n"
            "1️⃣ *Ім'я*\n"
            "2️⃣ *Коротко про вашу ситуацію* (професія, віза, яка цікавить)\n\n"
            "Надішліть одним повідомленням."
        ),
        "lead_received": (
            "✅ Дякуємо! Вашу заявку прийнято. "
            "Фахівець зв'яжеться з вами протягом робочого дня."
        ),

        "case_review_info": (
            "🆓 *Безкоштовний розбір вашої ситуації*\n\n"
            "⚠️ *Важливо:* усе, що ви тут напишете й додасте, *пересилається живому фахівцю* "
            "— не ШІ-асистенту. Відповіді в боті не буде — експерт зв'яжеться особисто.\n\n"
            "_Якщо хочете поставити питання ШІ — натисніть «⬅️ До меню» і оберіть «❓ Запитати про візу»._\n\n"
            "Опишіть свою ситуацію (професія, досвід, цілі) та за бажанням додайте документи — "
            "CV, дипломи, статті, нагороди, рекомендаційні листи.\n\n"
            "📎 *Як прикріпити файл:* натисніть скріпку ліворуч від поля введення повідомлення внизу екрана → "
            "оберіть «Файл» або «Фото» → надішліть. Приймаються PDF, DOCX, JPG, PNG та ін. "
            "до 2 ГБ за файл.\n\n"
            "Можна надіслати *декількома повідомленнями*. Коли завершите — натисніть *«Завершити надсилання»*.\n\n"
            "_Фахівець зв'яжеться протягом 1-2 робочих днів._"
        ),
        "case_review_forwarded": (
            "✓ Передав фахівцю. Він відповість особисто (не через бот) протягом "
            "1-2 робочих днів.\n\n"
            "Можна надіслати ще матеріали або натиснути «Завершити надсилання»."
        ),
        "case_review_forward_failed": (
            "⚠️ Не вдалося передати це повідомлення фахівцю. "
            "Спробуйте ще раз або напишіть текстом у «Записатися на консультацію»."
        ),
        "case_review_done": (
            "✅ Дякуємо! Експерт вивчить вашу заявку і зв'яжеться з вами протягом "
            "1-2 робочих днів."
        ),
        "case_button_inactive": "Ця кнопка вже неактивна. Оберіть дію:",
        "booking_file_ok": "✓ Файл отримано. Якщо ще не надіслали ім'я та опис — надішліть одним повідомленням.",
        "booking_file_failed": (
            "⚠️ Не вдалося передати файл фахівцю. Спробуйте ще раз "
            "або опишіть ситуацію текстом."
        ),
        "attachment_hint": (
            "Щоб надіслати документи — оберіть у меню «🆓 Безкоштовний розбір ситуації» "
            "або «📞 Записатися на консультацію»."
        ),

        "quiz_intro_eb1a": (
            "*EB-1A* — Extraordinary Ability. Потрібно відповідати мінімум *3 з 10* критеріїв "
            "+ позитивний Final Merits аналіз.\n\nВідповідайте «Так» або «Ні»."
        ),
        "quiz_intro_niw": (
            "*EB-2 NIW* — National Interest Waiver. Тест із справи *Matter of Dhanasar* (2016) — "
            "три обов'язкових елементи.\n\nВідповідайте «Так» або «Ні»."
        ),
        "quiz_intro_o1": (
            "*O-1A* — віза для людей з видатними здібностями (наука, бізнес, спорт). "
            "Потрібно мінімум *3 з 8* критеріїв.\n\nВідповідайте «Так» або «Ні»."
        ),
        "quiz_intro_e2": (
            "*E-2* — віза для інвесторів з країн, які мають торговельний договір зі США.\n\n"
            "🌍 *Країни колишнього СРСР і E-2:*\n"
            "✅ *Підпадають* (є договір): *Україна*, Грузія, Вірменія, Азербайджан, "
            "Казахстан, Киргизстан, Молдова, Естонія, Латвія, Литва.\n"
            "❌ *НЕ підпадають*: *Росія*, *Білорусь*, *Узбекистан*, *Таджикистан*, *Туркменістан*.\n\n"
            "На відміну від EB-категорій, *усі 7 вимог E-2 є обов'язковими*.\n\n"
            "Відповідайте «Так» або «Ні»."
        ),

        "eb1a_questions": [
            "🏆 У вас є великі національні або міжнародні нагороди/премії (окрім Нобелівської та подібних)?",
            "👥 Ви є членом асоціації, членство в якій вимагає видатних досягнень (на думку визнаних експертів)?",
            "📰 Про вас публікувалися матеріали у великих професійних або загальних ЗМІ?",
            "⚖️ Ви виступали суддею/рецензентом робіт інших фахівців у своїй галузі (журі, peer review тощо)?",
            "🔬 Чи маєте ви оригінальний внесок значної важливості у своїй галузі (винаходи, методики, публікації з цитуванням)?",
            "📚 Ви автор наукових статей у рецензованих журналах або великих виданнях?",
            "🎨 Ваші роботи виставлялися на художніх виставках чи показах?",
            "💼 Ви обіймали провідну або критично важливу роль у відомій організації?",
            "💰 Ваша зарплата/гонорар суттєво вища за середню у вашій галузі?",
            "🎭 У вас є комерційний успіх у виконавських мистецтвах (касові збори, тиражі тощо)?",
        ],
        "niw_questions": [
            "🇺🇸 Ваша діяльність має суттєву важливість і національне значення для США "
            "(охорона здоров'я, технології, економіка, культура, оборона тощо)?",
            "🎯 Ви добре підготовлені просувати цю діяльність (освіта, досвід, прогрес, "
            "плани, ресурси, інтерес з боку інвесторів/роботодавців)?",
            "⚖️ Чи є причини, з яких вимога PERM labor certification є недоцільною "
            "(терміновість, унікальність, ваш внесок переважує процедуру)?",
        ],
        "o1_questions": [
            "🏆 У вас є великі національні/міжнародні нагороди у вашій галузі?",
            "👥 Членство в асоціаціях, що вимагають видатних досягнень?",
            "📰 Публікації про вас у професійних або великих ЗМІ?",
            "🎯 Оригінальний внесок у галузь (науковий, бізнес, спортивний) значної важливості?",
            "⚖️ Ви виступали суддею/експертом робіт інших фахівців?",
            "📚 Авторство наукових статей у вашій галузі?",
            "💼 Робота у критичній/важливій ролі у відомих організаціях?",
            "💰 Висока зарплата/гонорар у порівнянні з колегами?",
        ],
        "e2_questions": [
            "🌍 Ви — громадянин країни, що має торговельний договір (E-2 treaty) зі США "
            "(наприклад, Україна, Грузія, Вірменія, Казахстан, Туреччина; *Росія — ні*, "
            "Білорусь — ні)?",
            "💵 Ви вже вклали кошти в бізнес у США або безповоротно задіяли їх "
            "(переведені, контракти підписані, обладнання куплено)? Кошти мають бути «at-risk».",
            "📊 Розмір інвестиції суттєвий і пропорційний вартості/типу бізнесу "
            "(для малого бізнесу зазвичай від $100–150K+, але залежить від сфери)?",
            "🏢 Це реальний діючий бізнес, що виробляє товари або послуги "
            "(не пасивне володіння нерухомістю чи цінними паперами)?",
            "👔 Ви володієте мінімум 50% бізнесу або маєте оперативний контроль "
            "(зможете «develop and direct» підприємство)?",
            "📈 Бізнес не marginal — тобто приносить або здатен приносити дохід більший "
            "за мінімальний для проживання інвестора та/або створює робочі місця/внесок в економіку США?",
            "✈️ Ви готові декларувати намір виїхати зі США по закінченні статусу E-2 "
            "(nonimmigrant intent)?",
        ],

        "pricing": (
            "💰 *Вартість послуг і терміни*\n\n"
            "*1. Консультація*\n"
            "${consult} (60–90 хв) — розбір за критеріями та стратегія за вашою категорією. "
            "Входить у вартість кейсу, якщо далі працюєте з нами.\n\n"
            "*2. Юридичні послуги (супровід петиції командою адвоката)*\n"
            "• *EB-1 (A, C)* або *EB-2 NIW*: *${petition}* — legal service / attorney fees "
            "за оцінку та підготовку петиції I-140 + evidence.\n"
            "• *I-485* (подача на грін-карту, коли черга доступна): "
            "*${member} за кожного члена сім'ї*.\n"
            "• Платежі прописуються в договорі — зазвичай 2–3 транші.\n\n"
            "*3. Держмита USCIS*\n"
            "• *I-140*: *$715*\n"
            "• Asylum program fee: *$300*\n"
            "• *I-485*: *$1 440*\n"
            "• *Premium Processing*: *$2 805*\n\n"
            "*4. Терміни*\n"
            "• I-140 — близько *12–16 місяців* у стандартному режимі.\n\n"
            "_Актуальні мита та терміни звіряйте на uscis.gov._"
        ),
    },

    # ────────────────────────────────────────────────────────────────── en
    "en": {
        "welcome": (
            "Hello! 🇺🇸\n"
            "I'm an AI assistant for U.S. visas. Main categories: *EB-1A*, *EB-2 NIW*, *EB-3*, *O-1*, *E-2*. "
            "I also answer general questions about *asylum*. I can help with:\n"
            "• qualification criteria\n"
            "• document requirements\n"
            "• common denial reasons and strategies\n\n"
            "Tell me about your situation or ask a specific question.\n\n"
            "⚠️ This information is for reference only and is not legal advice. "
            "Each case is unique and requires individual review."
        ),
        "language_saved": "✅ Language set: *English*",
        "menu_header": "Main menu:",
        "context_reset": "Context reset. Choose an action:",
        "lang_changed": "Choose your language:",

        "btn_ask": "❓ Ask a visa question",
        "btn_quiz": "📋 Evaluate my chances (quiz)",
        "btn_case_review": "🆓 Free case review",
        "btn_pricing": "💰 Pricing & timelines",
        "btn_book": "📞 Book a consultation",
        "btn_contact_human": "👤 Talk to a specialist",
        "human_prompt": (
            "✍️ Describe your question in one message — I'll pass it to our "
            "specialist, who will reply to you right here in this chat."
        ),
        "human_relayed": (
            "✅ Your message has been sent to a specialist. They'll reply here — "
            "feel free to add more or attach documents."
        ),
        "btn_back": "⬅️ Back to menu",
        "btn_checklist": "🎁 Free document checklist",
        "checklist_select": (
            "🎁 *Free petition document checklist.*\n\nChoose a visa:"
        ),
        "checklist_contact_prompt": (
            "📋 Great! Send your *name* and *email or phone* in one message — "
            "our specialists will send the checklist and answer any questions."
        ),
        "checklist_sent": (
            "✅ Thank you! Your checklist is below. Our specialists will also get in touch."
        ),
        "btn_support": "🛠 Tech support",
        "support_info": (
            "🛠 *Tech support*\n\n"
            "Send your question or any issue with the bot in your next message — "
            "it will be forwarded to support. You can attach a screenshot."
        ),
        "support_sent": (
            "✅ Your message has been sent to tech support. "
            "We'll get back to you soon."
        ),
        "support_failed": (
            "⚠️ Couldn't send your message. Please try again later."
        ),
        "btn_reminder_resume": "📋 Resume quiz",
        "reminder_quiz_incomplete": (
            "👋 You started the *{kind}* eligibility assessment but didn't finish. "
            "Want to complete it now?"
        ),
        "reminder_reengagement": (
            "👋 Yesterday you visited the AI assistant for US immigration. "
            "Can I answer any questions for you? "
            "I can also offer to book a consultation for you."
        ),
        "reminder_lead_followup": (
            "👋 Hello! You recently left a request — our specialists are ready "
            "to review your situation. Let us know what works better for you: "
            "a call or a chat. If new questions came up, ask them here."
        ),
        "btn_case_done": "✅ Finish sending",
        "btn_yes": "✅ Yes",
        "btn_no": "❌ No",
        "btn_lang": "🌐 Change language",

        "btn_quiz_eb1a": "EB-1A (Extraordinary Ability)",
        "btn_quiz_niw":  "EB-2 NIW (National Interest)",
        "btn_quiz_o1":   "O-1 (Extraordinary Ability)",
        "btn_quiz_e2":   "E-2 (Treaty Investor)",

        "ask_prompt": (
            "Ask your question about EB-1A, EB-2 NIW, O-1, E-2 or asylum. "
            "I answer based on USCIS rules.\n\n"
            "ℹ️ You can ask up to {total} questions. "
            "Once the limit is reached, we'll invite you to book a consultation with a specialist.\n\n"
            "_Questions left: {left}/{total}_"
        ),
        "quiz_start": "Chance evaluation by USCIS criteria.\n\nWhich visa quiz would you like to take?",
        "quiz_q_header": "*Question {n} of {total}:*\n\n{q}",
        "quiz_not_active": "The quiz is no longer active. Choose an action:",
        "in_quiz_warning": (
            "You're currently in a quiz — please answer with *«✅ Yes»* or *«❌ No»* "
            "buttons under the question above. To exit the quiz — /menu."
        ),
        "unknown_quiz": "Unknown quiz category.",

        "limit_reached": (
            "You've reached the limit of {total} questions. "
            "To continue, I recommend contacting a specialist — they'll review your case individually."
        ),
        "footer_remaining": "\n\n_Questions left: {left}/{total}_",
        "llm_error": "Temporary error contacting the knowledge base. Please try again in a minute.",
        "too_many_msgs": "⏳ Too many messages in a row. Please wait a moment and try again.",

        "lead_prompt": (
            "For a specialist to contact you, please provide:\n\n"
            "1️⃣ *Name*\n"
            "2️⃣ *Brief description of your situation* (profession, visa of interest)\n\n"
            "Send it in one message."
        ),
        "lead_received": (
            "✅ Thank you! Your request has been received. "
            "A specialist will contact you within one business day."
        ),

        "case_review_info": (
            "🆓 *Free review of your case*\n\n"
            "⚠️ *Important:* everything you write and attach here *is forwarded to a live specialist* "
            "— not to an AI assistant. There will be no reply in the bot — the expert will contact you personally.\n\n"
            "_To ask the AI — tap «⬅️ Back to menu» and choose «❓ Ask a visa question»._\n\n"
            "Describe your situation (profession, experience, goals) and attach documents if you wish — "
            "CV, diplomas, articles, awards, recommendation letters.\n\n"
            "📎 *How to attach a file:* tap the paper-clip icon to the left of the input field → "
            "choose «File» or «Photo» → send. PDF, DOCX, JPG, PNG and other formats up to 2 GB per file are accepted.\n\n"
            "You can send *multiple messages*. When done — tap *«Finish sending»*.\n\n"
            "_A specialist will be in touch within 1-2 business days._"
        ),
        "case_review_forwarded": (
            "✓ Forwarded to the specialist. They'll reply personally (not via the bot) "
            "within 1-2 business days.\n\n"
            "You can send more materials or tap «Finish sending»."
        ),
        "case_review_forward_failed": (
            "⚠️ Couldn't forward this message to the specialist. "
            "Please try again or describe the situation via «Book a consultation»."
        ),
        "case_review_done": (
            "✅ Thank you! An expert will review your request and contact you within "
            "1-2 business days."
        ),
        "case_button_inactive": "This button is no longer active. Choose an action:",
        "booking_file_ok": "✓ File received. If you haven't sent your name and description yet — send them in one message.",
        "booking_file_failed": (
            "⚠️ Couldn't forward the file to the specialist. Try again "
            "or describe the situation in text."
        ),
        "attachment_hint": (
            "To send documents — choose «🆓 Free case review» or "
            "«📞 Book a consultation» from the menu."
        ),

        "quiz_intro_eb1a": (
            "*EB-1A* — Extraordinary Ability. You need at least *3 out of 10* criteria "
            "plus a positive Final Merits analysis.\n\nAnswer «Yes» or «No»."
        ),
        "quiz_intro_niw": (
            "*EB-2 NIW* — National Interest Waiver. The test from *Matter of Dhanasar* (2016) — "
            "three mandatory elements.\n\nAnswer «Yes» or «No»."
        ),
        "quiz_intro_o1": (
            "*O-1A* — visa for individuals with extraordinary ability (science, business, sports). "
            "You need at least *3 out of 8* criteria.\n\nAnswer «Yes» or «No»."
        ),
        "quiz_intro_e2": (
            "*E-2* — visa for investors from countries with a U.S. treaty.\n\n"
            "🌍 *Post-Soviet countries and E-2:*\n"
            "✅ *Qualify*: Ukraine, Georgia, Armenia, Azerbaijan, "
            "Kazakhstan, Kyrgyzstan, Moldova, Estonia, Latvia, Lithuania.\n"
            "❌ *Do NOT qualify*: *Russia*, *Belarus*, *Uzbekistan*, *Tajikistan*, *Turkmenistan*.\n\n"
            "Unlike EB categories, *all 7 E-2 requirements are mandatory*.\n\n"
            "Answer «Yes» or «No»."
        ),

        "eb1a_questions": [
            "🏆 Do you have major national or international awards/prizes (other than the Nobel and similar)?",
            "👥 Are you a member of an association whose membership requires outstanding achievement (as judged by recognised experts)?",
            "📰 Have materials about you been published in major professional or general media?",
            "⚖️ Have you served as a judge/reviewer of the work of others in your field (jury, peer review, etc.)?",
            "🔬 Do you have original contributions of major significance in your field (inventions, methodologies, cited publications)?",
            "📚 Are you the author of scholarly articles in peer-reviewed journals or major media?",
            "🎨 Have your works been exhibited at artistic exhibitions or showcases?",
            "💼 Have you held a leading or critical role in a distinguished organisation?",
            "💰 Is your salary/compensation substantially higher than the average in your field?",
            "🎭 Do you have commercial success in the performing arts (box office, sales, etc.)?",
        ],
        "niw_questions": [
            "🇺🇸 Does your work have substantial merit and national importance to the U.S. (healthcare, technology, economy, culture, defense, etc.)?",
            "🎯 Are you well positioned to advance this work (education, experience, progress, plans, resources, interest from investors/employers)?",
            "⚖️ Are there reasons the PERM labor certification requirement is impractical (urgency, uniqueness, your contribution outweighs the process)?",
        ],
        "o1_questions": [
            "🏆 Do you have major national/international awards in your field?",
            "👥 Membership in associations requiring outstanding achievements?",
            "📰 Published material about you in professional or major media?",
            "🎯 Original contributions (scientific, business, athletic) of major significance?",
            "⚖️ Have you served as a judge/expert on the work of others?",
            "📚 Authorship of scholarly articles in your field?",
            "💼 Critical/essential role in distinguished organisations?",
            "💰 High salary/compensation compared to peers?",
        ],
        "e2_questions": [
            "🌍 Are you a citizen of a country with an E-2 treaty with the U.S. (e.g., Ukraine, Georgia, Armenia, Kazakhstan, Turkey; *Russia — no*, Belarus — no)?",
            "💵 Have you already invested funds in a U.S. business or irrevocably committed them (transferred, contracts signed, equipment purchased)? Funds must be «at-risk».",
            "📊 Is the investment substantial and proportional to the cost/type of business (typically $100–150K+ for small business, depends on sector)?",
            "🏢 Is this a real, operating business producing goods or services (not passive real-estate or securities holding)?",
            "👔 Do you own at least 50% or have operational control (able to «develop and direct» the enterprise)?",
            "📈 Is the business non-marginal — generating or capable of generating income above the minimum living requirement and/or creating jobs/contribution to the U.S. economy?",
            "✈️ Are you prepared to declare intent to depart the U.S. upon expiration of E-2 status (nonimmigrant intent)?",
        ],

        "pricing": (
            "💰 *Pricing & timelines*\n\n"
            "*1. Consultation*\n"
            "${consult} (60–90 min) — review of criteria and strategy for your category. "
            "Credited toward case fee if you retain us.\n\n"
            "*2. Legal services (petition preparation by attorney team)*\n"
            "• *EB-1 (A, C)* or *EB-2 NIW*: *${petition}* — attorney fees "
            "for evaluation and preparation of I-140 + evidence.\n"
            "• *I-485* (green-card filing when the queue is available): "
            "*${member} per family member*.\n"
            "• Payments are staged in the retainer — typically 2–3 tranches.\n\n"
            "*3. USCIS government fees*\n"
            "• *I-140*: *$715*\n"
            "• Asylum program fee: *$300*\n"
            "• *I-485*: *$1,440*\n"
            "• *Premium Processing*: *$2,805*\n\n"
            "*4. Timelines*\n"
            "• I-140 — about *12–16 months* in standard processing.\n\n"
            "_Verify current fees and timelines at uscis.gov._"
        ),
    },

    # ────────────────────────────────────────────────────────────────── es
    "es": {
        "welcome": (
            "¡Hola! 🇺🇸\n"
            "Soy un asistente de IA para visas de EE.UU. Categorías principales: *EB-1A*, *EB-2 NIW*, *EB-3*, *O-1*, *E-2*. "
            "También respondo preguntas generales sobre *asilo*. Puedo ayudar con:\n"
            "• criterios de calificación\n"
            "• requisitos documentales\n"
            "• causas comunes de denegación y estrategias\n\n"
            "Cuénteme su situación o haga una pregunta concreta.\n\n"
            "⚠️ Esta información es sólo de referencia y no constituye asesoría legal. "
            "Cada caso es único y requiere revisión individual."
        ),
        "language_saved": "✅ Idioma fijado: *Español*",
        "menu_header": "Menú principal:",
        "context_reset": "Contexto reiniciado. Elija una acción:",
        "lang_changed": "Elija su idioma:",

        "btn_ask": "❓ Preguntar sobre visas",
        "btn_quiz": "📋 Evaluar mis opciones (cuestionario)",
        "btn_case_review": "🆓 Revisión gratuita del caso",
        "btn_pricing": "💰 Precios y plazos",
        "btn_book": "📞 Reservar consulta",
        "btn_contact_human": "👤 Hablar con un especialista",
        "human_prompt": (
            "✍️ Describa su consulta en un mensaje — la enviaré a nuestro "
            "especialista, que le responderá aquí mismo, en este chat."
        ),
        "human_relayed": (
            "✅ Su mensaje fue enviado a un especialista. Le responderá aquí — "
            "puede escribir más o adjuntar documentos."
        ),
        "btn_back": "⬅️ Al menú",
        "btn_checklist": "🎁 Lista de documentos gratis",
        "checklist_select": (
            "🎁 *Lista gratuita de documentos para la petición.*\n\nElija una visa:"
        ),
        "checklist_contact_prompt": (
            "📋 ¡Genial! Envíe su *nombre* y *email o teléfono* en un solo mensaje — "
            "nuestros especialistas le enviarán la lista y responderán sus preguntas."
        ),
        "checklist_sent": (
            "✅ ¡Gracias! Su lista está abajo. Nuestros especialistas también se pondrán en contacto."
        ),
        "btn_support": "🛠 Soporte técnico",
        "support_info": (
            "🛠 *Soporte técnico*\n\n"
            "Escriba en su próximo mensaje su pregunta o problema con el bot — "
            "se enviará al soporte. Puede adjuntar una captura de pantalla."
        ),
        "support_sent": (
            "✅ Su mensaje se ha enviado al soporte técnico. "
            "Nos pondremos en contacto pronto."
        ),
        "support_failed": (
            "⚠️ No se pudo enviar el mensaje. Inténtelo de nuevo más tarde."
        ),
        "btn_reminder_resume": "📋 Continuar el cuestionario",
        "reminder_quiz_incomplete": (
            "👋 Empezaste la evaluación de elegibilidad para *{kind}* pero no la terminaste. "
            "¿Quieres completarla ahora?"
        ),
        "reminder_reengagement": (
            "👋 Ayer visitó el asistente de IA para inmigración a EE. UU. "
            "¿Puedo responder a alguna pregunta? "
            "También puedo ofrecerle reservar una consulta."
        ),
        "reminder_lead_followup": (
            "👋 ¡Hola! Recientemente dejó una solicitud — nuestros especialistas "
            "están listos para revisar su situación. Díganos qué prefiere: "
            "una llamada o un chat. Si surgieron nuevas preguntas, hágalas aquí."
        ),
        "btn_case_done": "✅ Terminar envío",
        "btn_yes": "✅ Sí",
        "btn_no": "❌ No",
        "btn_lang": "🌐 Cambiar idioma",

        "btn_quiz_eb1a": "EB-1A (Habilidad Extraordinaria)",
        "btn_quiz_niw":  "EB-2 NIW (Interés Nacional)",
        "btn_quiz_o1":   "O-1 (Habilidad Extraordinaria)",
        "btn_quiz_e2":   "E-2 (Inversor por Tratado)",

        "ask_prompt": (
            "Haga su pregunta sobre EB-1A, EB-2 NIW, O-1, E-2 o asilo. "
            "Respondo con base en las reglas de USCIS.\n\n"
            "ℹ️ Puede hacer hasta {total} preguntas. "
            "Cuando se agote el límite, le propondremos agendar una consulta con un especialista.\n\n"
            "_Preguntas restantes: {left}/{total}_"
        ),
        "quiz_start": "Evaluación de posibilidades según criterios de USCIS.\n\n¿Qué cuestionario quiere hacer?",
        "quiz_q_header": "*Pregunta {n} de {total}:*\n\n{q}",
        "quiz_not_active": "El cuestionario ya no está activo. Elija una acción:",
        "in_quiz_warning": (
            "Está realizando un cuestionario — responda con los botones *«✅ Sí»* o *«❌ No»* "
            "debajo de la pregunta. Para salir — /menu."
        ),
        "unknown_quiz": "Categoría de cuestionario desconocida.",

        "limit_reached": (
            "Ha alcanzado el límite de {total} preguntas. "
            "Para continuar, le recomiendo contactar a un especialista — revisará su caso individualmente."
        ),
        "footer_remaining": "\n\n_Preguntas restantes: {left}/{total}_",
        "llm_error": "Error temporal al consultar la base de conocimientos. Intente de nuevo en un minuto.",
        "too_many_msgs": "⏳ Demasiados mensajes seguidos. Espere un momento e inténtelo de nuevo.",

        "lead_prompt": (
            "Para que un especialista le contacte, por favor indique:\n\n"
            "1️⃣ *Nombre*\n"
            "2️⃣ *Breve descripción de su situación* (profesión, visa de interés)\n\n"
            "Envíelo en un solo mensaje."
        ),
        "lead_received": (
            "✅ ¡Gracias! Su solicitud ha sido recibida. "
            "Un especialista se pondrá en contacto durante el día hábil."
        ),

        "case_review_info": (
            "🆓 *Revisión gratuita de su caso*\n\n"
            "⚠️ *Importante:* todo lo que escriba y adjunte aquí *se reenvía a un especialista humano* "
            "— no a un asistente de IA. No habrá respuesta en el bot — el experto le contactará personalmente.\n\n"
            "_Si desea preguntar a la IA — toque «⬅️ Al menú» y elija «❓ Preguntar sobre visas»._\n\n"
            "Describa su situación (profesión, experiencia, objetivos) y adjunte documentos si desea — "
            "CV, diplomas, artículos, premios, cartas de recomendación.\n\n"
            "📎 *Cómo adjuntar un archivo:* toque el clip a la izquierda del campo de texto → "
            "elija «Archivo» o «Foto» → envíe. Se aceptan PDF, DOCX, JPG, PNG y otros hasta 2 GB por archivo.\n\n"
            "Puede enviar *varios mensajes*. Cuando termine — toque *«Terminar envío»*.\n\n"
            "_Un especialista le contactará en 1-2 días hábiles._"
        ),
        "case_review_forwarded": (
            "✓ Reenviado al especialista. Le responderá personalmente (no por el bot) "
            "en 1-2 días hábiles.\n\n"
            "Puede enviar más materiales o tocar «Terminar envío»."
        ),
        "case_review_forward_failed": (
            "⚠️ No se pudo reenviar este mensaje al especialista. "
            "Intente de nuevo o describa su situación en «Reservar consulta»."
        ),
        "case_review_done": (
            "✅ ¡Gracias! Un experto revisará su solicitud y le contactará "
            "en 1-2 días hábiles."
        ),
        "case_button_inactive": "Este botón ya no está activo. Elija una acción:",
        "booking_file_ok": "✓ Archivo recibido. Si aún no envió su nombre y descripción — hágalo en un mensaje.",
        "booking_file_failed": (
            "⚠️ No se pudo reenviar el archivo al especialista. Intente de nuevo "
            "o describa la situación por texto."
        ),
        "attachment_hint": (
            "Para enviar documentos — elija en el menú «🆓 Revisión gratuita del caso» "
            "o «📞 Reservar consulta»."
        ),

        "quiz_intro_eb1a": (
            "*EB-1A* — Habilidad Extraordinaria. Necesita al menos *3 de 10* criterios "
            "más un análisis Final Merits positivo.\n\nResponda «Sí» o «No»."
        ),
        "quiz_intro_niw": (
            "*EB-2 NIW* — National Interest Waiver. El test del caso *Matter of Dhanasar* (2016) — "
            "tres elementos obligatorios.\n\nResponda «Sí» o «No»."
        ),
        "quiz_intro_o1": (
            "*O-1A* — visa para personas con habilidad extraordinaria (ciencia, negocios, deportes). "
            "Necesita al menos *3 de 8* criterios.\n\nResponda «Sí» o «No»."
        ),
        "quiz_intro_e2": (
            "*E-2* — visa para inversores de países con tratado comercial con EE.UU.\n\n"
            "🌍 *Países de la ex-URSS y E-2:*\n"
            "✅ *Califican*: Ucrania, Georgia, Armenia, Azerbaiyán, "
            "Kazajistán, Kirguistán, Moldavia, Estonia, Letonia, Lituania.\n"
            "❌ *NO califican*: *Rusia*, *Bielorrusia*, *Uzbekistán*, *Tayikistán*, *Turkmenistán*.\n\n"
            "A diferencia de las categorías EB, *los 7 requisitos de E-2 son obligatorios*.\n\n"
            "Responda «Sí» o «No»."
        ),

        "eb1a_questions": [
            "🏆 ¿Tiene premios/galardones nacionales o internacionales importantes (salvo Nobel y similares)?",
            "👥 ¿Es miembro de una asociación cuya afiliación exige logros extraordinarios (según expertos reconocidos)?",
            "📰 ¿Se han publicado materiales sobre usted en medios profesionales o generales importantes?",
            "⚖️ ¿Ha actuado como juez/revisor de trabajos de otros en su campo (jurado, peer review, etc.)?",
            "🔬 ¿Tiene contribuciones originales de gran importancia en su campo (invenciones, metodologías, publicaciones citadas)?",
            "📚 ¿Es autor de artículos científicos en revistas revisadas por pares o medios importantes?",
            "🎨 ¿Sus obras se han expuesto en exhibiciones artísticas?",
            "💼 ¿Ha ocupado un rol principal o crítico en una organización destacada?",
            "💰 ¿Su salario/honorarios es sustancialmente superior al promedio en su campo?",
            "🎭 ¿Tiene éxito comercial en las artes escénicas (taquilla, ventas, etc.)?",
        ],
        "niw_questions": [
            "🇺🇸 ¿Su actividad tiene mérito sustancial e importancia nacional para EE.UU. (salud, tecnología, economía, cultura, defensa, etc.)?",
            "🎯 ¿Está bien posicionado para avanzar esta actividad (educación, experiencia, progreso, planes, recursos, interés de inversores/empleadores)?",
            "⚖️ ¿Hay razones por las que el requisito de PERM labor certification es impractico (urgencia, singularidad, su aporte supera el proceso)?",
        ],
        "o1_questions": [
            "🏆 ¿Tiene premios nacionales/internacionales importantes en su campo?",
            "👥 ¿Pertenece a asociaciones que exigen logros extraordinarios?",
            "📰 ¿Publicaciones sobre usted en medios profesionales o importantes?",
            "🎯 ¿Contribuciones originales (científicas, empresariales, deportivas) de gran importancia?",
            "⚖️ ¿Ha actuado como juez/experto sobre el trabajo de otros?",
            "📚 ¿Autoría de artículos científicos en su campo?",
            "💼 ¿Rol crítico/esencial en organizaciones destacadas?",
            "💰 ¿Salario/honorarios altos comparados con sus pares?",
        ],
        "e2_questions": [
            "🌍 ¿Es ciudadano de un país con tratado E-2 con EE.UU. (p. ej., Ucrania, Georgia, Armenia, Kazajistán, Turquía; *Rusia — no*, Bielorrusia — no)?",
            "💵 ¿Ya invirtió fondos en un negocio en EE.UU. o los comprometió irrevocablemente (transferidos, contratos firmados, equipo comprado)? Los fondos deben estar «at-risk».",
            "📊 ¿La inversión es sustancial y proporcional al costo/tipo de negocio (típicamente $100–150K+ para pequeño negocio, depende del sector)?",
            "🏢 ¿Es un negocio real y operativo produciendo bienes o servicios (no tenencia pasiva de inmuebles o valores)?",
            "👔 ¿Posee al menos 50% o tiene control operativo (capaz de «develop and direct» la empresa)?",
            "📈 ¿El negocio no es marginal — genera o puede generar ingresos por encima del mínimo de subsistencia y/o crea empleos/aporte a la economía de EE.UU.?",
            "✈️ ¿Está dispuesto a declarar intención de salir de EE.UU. al vencer el estatus E-2 (nonimmigrant intent)?",
        ],

        "pricing": (
            "💰 *Precios y plazos*\n\n"
            "*1. Consulta*\n"
            "${consult} (60–90 min) — análisis de criterios y estrategia para su categoría. "
            "Se acredita al total del caso si continúa con nosotros.\n\n"
            "*2. Servicios legales (preparación de petición por equipo de abogados)*\n"
            "• *EB-1 (A, C)* o *EB-2 NIW*: *${petition}* — honorarios por "
            "evaluación y preparación de I-140 + evidencia.\n"
            "• *I-485* (green card cuando haya cupo): *${member} por familiar*.\n"
            "• Pagos escalonados en el contrato — normalmente 2–3 tramos.\n\n"
            "*3. Aranceles gubernamentales USCIS*\n"
            "• *I-140*: *$715*\n"
            "• Asylum program fee: *$300*\n"
            "• *I-485*: *$1,440*\n"
            "• *Premium Processing*: *$2,805*\n\n"
            "*4. Plazos*\n"
            "• I-140 — unos *12–16 meses* en trámite estándar.\n\n"
            "_Verifique aranceles y plazos vigentes en uscis.gov._"
        ),
    },

}


# ── EB-3 quiz strings (added as a full category). Injected into every language
# block below so we don't have to hand-edit all language dicts. Any language missing
# here falls back to English via the loop. Checklist content for EB-3 lives in
# prompts.CHECKLISTS (Russian, auto-translated at runtime), like the others.
_EB3: dict[str, dict[str, object]] = {
  "ru": {"btn_quiz_eb3": "EB-3 (Skilled / Professional)", "quiz_intro_eb3": "*EB-3* — рабочая иммиграционная виза (Skilled Workers / Professionals / Other Workers). Требует постоянного предложения работы от работодателя США и трудовой сертификации PERM; петицию подаёт работодатель.\n\nКак и у E-2, *все требования обязательны*.\n\nОтвечайте «Да» или «Нет».", "eb3_questions": ["💼 У вас есть постоянное полноценное (full-time) предложение работы от работодателя в США — или работодатель готов его дать?", "📝 Работодатель готов оформить трудовую сертификацию PERM и подать за вас петицию I-140 (EB-3 без работодателя-спонсора невозможна)?", "🎓 Вы соответствуете требованиям позиции: степень бакалавра (Professionals), либо ≥2 лет опыта/обучения (Skilled), либо позиция требует <2 лет подготовки (Other Workers)?", "💵 Работодатель готов платить не ниже prevailing wage (официальной средней зарплаты по этой позиции и региону)?", "🔍 Нет доступных квалифицированных работников из США на эту позицию (это проверяется в ходе PERM)?"]},
  "uk": {"btn_quiz_eb3": "EB-3 (Skilled / Professional)", "quiz_intro_eb3": "*EB-3* — робоча імміграційна віза (Skilled Workers / Professionals / Other Workers). Вимагає постійної пропозиції роботи від роботодавця США та трудової сертифікації PERM; петицію подає роботодавець.\n\nЯк і в E-2, *усі вимоги обов'язкові*.\n\nВідповідайте «Так» або «Ні».", "eb3_questions": ["💼 У вас є постійна повноцінна (full-time) пропозиція роботи від роботодавця у США — або роботодавець готовий її надати?", "📝 Роботодавець готовий оформити трудову сертифікацію PERM та подати за вас петицію I-140 (EB-3 без роботодавця-спонсора неможлива)?", "🎓 Ви відповідаєте вимогам позиції: ступінь бакалавра (Professionals), або ≥2 років досвіду/навчання (Skilled), або позиція вимагає <2 років підготовки (Other Workers)?", "💵 Роботодавець готовий платити не нижче prevailing wage (офіційної середньої зарплати за цією позицією та регіоном)?", "🔍 Немає доступних кваліфікованих працівників зі США на цю позицію (це перевіряється в ході PERM)?"]},
  "en": {"btn_quiz_eb3": "EB-3 (Skilled / Professional)", "quiz_intro_eb3": "*EB-3* — employment-based immigrant visa (Skilled Workers / Professionals / Other Workers). Requires a permanent job offer from a US employer and a PERM labor certification; the employer files the petition.\n\nLike E-2, *all requirements are mandatory*.\n\nAnswer \"Yes\" or \"No\".", "eb3_questions": ["💼 Do you have a permanent full-time job offer from a US employer — or is an employer ready to provide one?", "📝 Is the employer willing to obtain a PERM labor certification and file an I-140 petition for you (EB-3 is impossible without a sponsoring employer)?", "🎓 Do you meet the position's requirements: a bachelor's degree (Professionals), or ≥2 years of experience/training (Skilled), or a position requiring <2 years of training (Other Workers)?", "💵 Is the employer ready to pay at least the prevailing wage (the official average wage for this position and region)?", "🔍 Are there no qualified US workers available for this position (this is tested during PERM)?"]},
  "es": {"btn_quiz_eb3": "EB-3 (Skilled / Professional)", "quiz_intro_eb3": "*EB-3* — visa de inmigrante por empleo (Skilled Workers / Professionals / Other Workers). Requiere una oferta de trabajo permanente de un empleador en EE. UU. y una certificación laboral PERM; el empleador presenta la petición.\n\nAl igual que E-2, *todos los requisitos son obligatorios*.\n\nResponda «Sí» o «No».", "eb3_questions": ["💼 ¿Tiene una oferta de trabajo permanente a tiempo completo (full-time) de un empleador en EE. UU., o un empleador está dispuesto a ofrecerla?", "📝 ¿El empleador está dispuesto a obtener una certificación laboral PERM y presentar una petición I-140 por usted (EB-3 es imposible sin un empleador patrocinador)?", "🎓 ¿Cumple los requisitos del puesto: un título de licenciatura (Professionals), o ≥2 años de experiencia/formación (Skilled), o un puesto que requiere <2 años de preparación (Other Workers)?", "💵 ¿El empleador está dispuesto a pagar al menos el prevailing wage (el salario medio oficial para este puesto y región)?", "🔍 ¿No hay trabajadores estadounidenses cualificados disponibles para este puesto (esto se verifica durante el PERM)?"]},
}

# Inject EB-3 keys into each language block (English fallback for any gaps).
for _code in list(T):
    T[_code].update(_EB3.get(_code, _EB3["en"]))


def t(key: str, lang: str) -> object:
    """Look up a translation string; fall back to English, then to key."""
    lang = lang if lang in T else "en"
    val = T[lang].get(key)
    if val is None:
        val = T["en"].get(key, key)
    return val


def pricing_text(lang: str) -> str:
    """The pricing message with firm service prices substituted from config
    (the {consult}/{petition}/{member} placeholders). Government USCIS fees in
    the same text are literal and untouched."""
    import config
    return str(t("pricing", lang)).format(**config.prices())


def welcome_text(lang: str) -> str:
    """The greeting, optionally prefixed with the firm's brand line when
    FIRM_NAME is configured (white-label). Unbranded deploys are unchanged."""
    import config
    body = str(t("welcome", lang))
    if config.FIRM_NAME:
        # Escape MarkdownV1 specials so a firm name like "O_Brien & Co*" can't
        # break parsing and drop the whole greeting.
        firm = config.FIRM_NAME
        for ch in ("\\", "*", "_", "`", "["):
            firm = firm.replace(ch, "\\" + ch)
        return f"*{firm}*\n\n{body}"
    return body


def normalize_lang(lang: str | None) -> str:
    """Return a valid language code; default to DEFAULT_LANG if unknown."""
    if lang and lang in LANG_CODES:
        return lang
    return DEFAULT_LANG

