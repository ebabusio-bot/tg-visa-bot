# -*- coding: utf-8 -*-
"""Multi-language UI strings. Admin-facing text stays Russian in bot.py."""

DEFAULT_LANG = "ru"

# (code, flag, native_name, display_for_button)
LANGUAGES: list[tuple[str, str, str]] = [
    ("en", "🇬🇧", "English"),
    ("es", "🇪🇸", "Español"),
    ("fr", "🇫🇷", "Français"),
    ("uk", "🇺🇦", "Українська"),
    ("ru", "🇷🇺", "Русский"),
    ("pt", "🇵🇹", "Português"),
    ("ht", "🇭🇹", "Kreyòl Ayisyen"),
    ("hi", "🇮🇳", "हिन्दी"),
]

LANG_CODES = {c for c, _, _ in LANGUAGES}

# For admin-facing text (Russian).
LANG_NAMES_RU: dict[str, str] = {
    "ru": "русский",
    "uk": "украинский",
    "en": "английский",
    "es": "испанский",
    "fr": "французский",
    "ht": "гаитянский креольский",
    "pt": "португальский",
    "hi": "хинди",
}

LANG_FLAGS: dict[str, str] = {c: f for c, f, _ in LANGUAGES}

# For each language, the native name of that language (used in the LLM
# language directive, e.g. "respond in Español").
LANG_NATIVE: dict[str, str] = {c: n for c, _, n in LANGUAGES}

# Multilingual initial language prompt (shown before any greeting, in every
# supported language at once so the user can recognise their own).
LANGUAGE_PICKER_PROMPT = (
    "🌐 Please choose your language · Por favor, elija su idioma · "
    "Veuillez choisir votre langue · Будь ласка, оберіть мову · "
    "Пожалуйста, выберите язык · Escolha o seu idioma · "
    "Tanpri chwazi lang ou · कृपया अपनी भाषा चुनें"
)


# Full string dictionary. Each language has the same set of keys.
# Fallback: if a key is missing for a language, falls back to English.
T: dict[str, dict[str, object]] = {

    # ────────────────────────────────────────────────────────────────── ru
    "ru": {
        "welcome": (
            "Здравствуйте! 🇺🇸\n"
            "Я — ИИ-помощник по визам США. Основные категории: *EB-1A*, *EB-2 NIW*, *O-1*, *E-2*. "
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
        "btn_back": "⬅️ В меню",
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
            "_Осталось сообщений сегодня: {left}/{total}_"
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
            "Вы достигли дневного лимита в 15 сообщений. "
            "Для продолжения рекомендую связаться со специалистом — он разберёт вашу ситуацию индивидуально.\n\n"
            "Лимит сбросится через 24 часа."
        ),
        "footer_remaining": "\n\n_Осталось сегодня: {left}/{total}_",
        "llm_error": "Временная ошибка при обращении к базе знаний. Попробуйте ещё раз через минуту.",

        "lead_prompt": (
            "Чтобы специалист связался с вами, пожалуйста, укажите:\n\n"
            "1️⃣ *Имя*\n"
            "2️⃣ *Коротко о вашей ситуации* (профессия, виза, которая интересует)\n\n"
            "Отправьте одним сообщением."
        ),
        "lead_received": (
            "✅ Спасибо! Ваша заявка принята. "
            "Специалист свяжется с вами в течение рабочего дня."
        ),

        "case_review_info": (
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
            "_Специалист свяжется в течение 1-2 рабочих дней._"
        ),
        "case_review_forwarded": (
            "✓ Передал специалисту. Он ответит лично (не через бот) в течение "
            "1-2 рабочих дней.\n\n"
            "Можно отправить ещё материалы или нажать «Завершить отправку»."
        ),
        "case_review_forward_failed": (
            "⚠️ Не удалось передать это сообщение специалисту. "
            "Попробуйте ещё раз или напишите текстом в «Записаться на консультацию»."
        ),
        "case_review_done": (
            "✅ Спасибо! Эксперт изучит вашу заявку и свяжется с вами в течение "
            "1-2 рабочих дней."
        ),
        "case_button_inactive": "Эта кнопка уже не активна. Выберите действие:",
        "booking_file_ok": "✓ Файл получен. Если ещё не прислали имя и описание — пришлите одним сообщением.",
        "booking_file_failed": (
            "⚠️ Не удалось передать файл специалисту. Попробуйте ещё раз "
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
            "$300 (60–90 мин) — разбор по критериям и стратегия по вашей категории. "
            "Входит в стоимость кейса, если далее работаете с нами.\n\n"
            "*2. Юридические услуги (сопровождение петиции командой адвоката)*\n"
            "• *EB-1 (A, C)* или *EB-2 NIW*: *$15 000* — legal service / attorney fees "
            "за оценку и подготовку петиции I-140 + evidence.\n"
            "• *I-485* (подача на грин-карту, когда очередь доступна): "
            "*$500 за каждого члена семьи*.\n"
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
            "Я — ШІ-помічник з американських віз. Основні категорії: *EB-1A*, *EB-2 NIW*, *O-1*, *E-2*. "
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
        "btn_back": "⬅️ До меню",
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
            "_Залишилось повідомлень сьогодні: {left}/{total}_"
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
            "Ви досягли денного ліміту у 15 повідомлень. "
            "Для продовження рекомендую звернутися до фахівця — він розбере вашу ситуацію індивідуально.\n\n"
            "Ліміт скинеться через 24 години."
        ),
        "footer_remaining": "\n\n_Залишилось сьогодні: {left}/{total}_",
        "llm_error": "Тимчасова помилка при зверненні до бази знань. Спробуйте ще раз через хвилину.",

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
            "$300 (60–90 хв) — розбір за критеріями та стратегія за вашою категорією. "
            "Входить у вартість кейсу, якщо далі працюєте з нами.\n\n"
            "*2. Юридичні послуги (супровід петиції командою адвоката)*\n"
            "• *EB-1 (A, C)* або *EB-2 NIW*: *$15 000* — legal service / attorney fees "
            "за оцінку та підготовку петиції I-140 + evidence.\n"
            "• *I-485* (подача на грін-карту, коли черга доступна): "
            "*$500 за кожного члена сім'ї*.\n"
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
            "I'm an AI assistant for U.S. visas. Main categories: *EB-1A*, *EB-2 NIW*, *O-1*, *E-2*. "
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
        "btn_back": "⬅️ Back to menu",
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
            "_Messages left today: {left}/{total}_"
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
            "You've reached the daily limit of 15 messages. "
            "To continue, I recommend contacting a specialist — they'll review your case individually.\n\n"
            "Limit resets in 24 hours."
        ),
        "footer_remaining": "\n\n_Remaining today: {left}/{total}_",
        "llm_error": "Temporary error contacting the knowledge base. Please try again in a minute.",

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
            "$300 (60–90 min) — review of criteria and strategy for your category. "
            "Credited toward case fee if you retain us.\n\n"
            "*2. Legal services (petition preparation by attorney team)*\n"
            "• *EB-1 (A, C)* or *EB-2 NIW*: *$15 000* — attorney fees "
            "for evaluation and preparation of I-140 + evidence.\n"
            "• *I-485* (green-card filing when the queue is available): "
            "*$500 per family member*.\n"
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
            "Soy un asistente de IA para visas de EE.UU. Categorías principales: *EB-1A*, *EB-2 NIW*, *O-1*, *E-2*. "
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
        "btn_back": "⬅️ Al menú",
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
            "_Mensajes restantes hoy: {left}/{total}_"
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
            "Ha alcanzado el límite diario de 15 mensajes. "
            "Para continuar, le recomiendo contactar a un especialista — revisará su caso individualmente.\n\n"
            "El límite se restablece en 24 horas."
        ),
        "footer_remaining": "\n\n_Restantes hoy: {left}/{total}_",
        "llm_error": "Error temporal al consultar la base de conocimientos. Intente de nuevo en un minuto.",

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
            "$300 (60–90 min) — análisis de criterios y estrategia para su categoría. "
            "Se acredita al total del caso si continúa con nosotros.\n\n"
            "*2. Servicios legales (preparación de petición por equipo de abogados)*\n"
            "• *EB-1 (A, C)* o *EB-2 NIW*: *$15 000* — honorarios por "
            "evaluación y preparación de I-140 + evidencia.\n"
            "• *I-485* (green card cuando haya cupo): *$500 por familiar*.\n"
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

    # ────────────────────────────────────────────────────────────────── fr
    "fr": {
        "welcome": (
            "Bonjour ! 🇺🇸\n"
            "Je suis un assistant IA pour les visas américains. Catégories principales : *EB-1A*, *EB-2 NIW*, *O-1*, *E-2*. "
            "Je réponds aussi aux questions générales sur l'*asile*. Je peux aider sur :\n"
            "• les critères de qualification\n"
            "• les exigences documentaires\n"
            "• les motifs de refus courants et les stratégies\n\n"
            "Parlez-moi de votre situation ou posez une question précise.\n\n"
            "⚠️ Information à titre indicatif, pas un conseil juridique. "
            "Chaque cas est unique et nécessite un examen individuel."
        ),
        "language_saved": "✅ Langue définie : *Français*",
        "menu_header": "Menu principal :",
        "context_reset": "Contexte réinitialisé. Choisissez une action :",
        "lang_changed": "Choisissez votre langue :",

        "btn_ask": "❓ Poser une question visa",
        "btn_quiz": "📋 Évaluer mes chances (questionnaire)",
        "btn_case_review": "🆓 Revue gratuite du dossier",
        "btn_pricing": "💰 Tarifs et délais",
        "btn_book": "📞 Réserver une consultation",
        "btn_back": "⬅️ Au menu",
        "btn_case_done": "✅ Terminer l'envoi",
        "btn_yes": "✅ Oui",
        "btn_no": "❌ Non",
        "btn_lang": "🌐 Changer de langue",

        "btn_quiz_eb1a": "EB-1A (Capacité Extraordinaire)",
        "btn_quiz_niw":  "EB-2 NIW (Intérêt National)",
        "btn_quiz_o1":   "O-1 (Capacité Extraordinaire)",
        "btn_quiz_e2":   "E-2 (Investisseur par Traité)",

        "ask_prompt": (
            "Posez votre question sur EB-1A, EB-2 NIW, O-1, E-2 ou l'asile. "
            "Je réponds selon les règles de l'USCIS.\n\n"
            "_Messages restants aujourd'hui : {left}/{total}_"
        ),
        "quiz_start": "Évaluation selon les critères USCIS.\n\nQuel questionnaire voulez-vous faire ?",
        "quiz_q_header": "*Question {n} sur {total} :*\n\n{q}",
        "quiz_not_active": "Le questionnaire n'est plus actif. Choisissez une action :",
        "in_quiz_warning": (
            "Vous êtes dans un questionnaire — répondez avec les boutons *«✅ Oui»* ou *«❌ Non»* "
            "sous la question. Pour sortir — /menu."
        ),
        "unknown_quiz": "Catégorie de questionnaire inconnue.",

        "limit_reached": (
            "Vous avez atteint la limite quotidienne de 15 messages. "
            "Pour continuer, contactez un spécialiste — il examinera votre cas individuellement.\n\n"
            "La limite se réinitialise sous 24 heures."
        ),
        "footer_remaining": "\n\n_Restants aujourd'hui : {left}/{total}_",
        "llm_error": "Erreur temporaire d'accès à la base de connaissances. Réessayez dans une minute.",

        "lead_prompt": (
            "Pour qu'un spécialiste vous contacte, veuillez indiquer :\n\n"
            "1️⃣ *Nom*\n"
            "2️⃣ *Brève description de votre situation* (profession, visa souhaité)\n\n"
            "Envoyez le tout en un seul message."
        ),
        "lead_received": (
            "✅ Merci ! Votre demande a été reçue. "
            "Un spécialiste vous contactera dans la journée ouvrée."
        ),

        "case_review_info": (
            "🆓 *Revue gratuite de votre cas*\n\n"
            "⚠️ *Important :* tout ce que vous écrivez et joignez ici *est transmis à un spécialiste humain* "
            "— pas à un assistant IA. Pas de réponse dans le bot — l'expert vous contactera personnellement.\n\n"
            "_Pour une question à l'IA — appuyez sur «⬅️ Au menu» et choisissez «❓ Poser une question visa»._\n\n"
            "Décrivez votre situation (profession, expérience, objectifs) et joignez des documents si vous le souhaitez — "
            "CV, diplômes, articles, prix, lettres de recommandation.\n\n"
            "📎 *Comment joindre un fichier :* appuyez sur le trombone à gauche du champ de saisie → "
            "choisissez « Fichier » ou « Photo » → envoyez. PDF, DOCX, JPG, PNG et autres acceptés jusqu'à 2 Go par fichier.\n\n"
            "Vous pouvez envoyer *plusieurs messages*. Quand vous avez fini — appuyez sur *«Terminer l'envoi»*.\n\n"
            "_Un spécialiste vous contactera sous 1-2 jours ouvrés._"
        ),
        "case_review_forwarded": (
            "✓ Transmis au spécialiste. Il répondra personnellement (pas via le bot) "
            "sous 1-2 jours ouvrés.\n\n"
            "Vous pouvez envoyer d'autres documents ou appuyer sur « Terminer l'envoi »."
        ),
        "case_review_forward_failed": (
            "⚠️ Impossible de transmettre ce message au spécialiste. "
            "Réessayez ou décrivez la situation via « Réserver une consultation »."
        ),
        "case_review_done": (
            "✅ Merci ! Un expert étudiera votre demande et vous contactera "
            "sous 1-2 jours ouvrés."
        ),
        "case_button_inactive": "Ce bouton n'est plus actif. Choisissez une action :",
        "booking_file_ok": "✓ Fichier reçu. Si vous n'avez pas encore envoyé nom et description — faites-le en un message.",
        "booking_file_failed": (
            "⚠️ Impossible de transmettre le fichier au spécialiste. Réessayez "
            "ou décrivez la situation par texte."
        ),
        "attachment_hint": (
            "Pour envoyer des documents — choisissez dans le menu « 🆓 Revue gratuite du dossier » "
            "ou « 📞 Réserver une consultation »."
        ),

        "quiz_intro_eb1a": (
            "*EB-1A* — Capacité Extraordinaire. Il faut au moins *3 critères sur 10* "
            "plus une analyse Final Merits positive.\n\nRépondez « Oui » ou « Non »."
        ),
        "quiz_intro_niw": (
            "*EB-2 NIW* — National Interest Waiver. Le test issu de *Matter of Dhanasar* (2016) — "
            "trois éléments obligatoires.\n\nRépondez « Oui » ou « Non »."
        ),
        "quiz_intro_o1": (
            "*O-1A* — visa pour personnes aux capacités extraordinaires (science, business, sport). "
            "Il faut au moins *3 critères sur 8*.\n\nRépondez « Oui » ou « Non »."
        ),
        "quiz_intro_e2": (
            "*E-2* — visa pour investisseurs des pays liés par un traité commercial avec les USA.\n\n"
            "🌍 *Pays de l'ex-URSS et E-2 :*\n"
            "✅ *Éligibles* : Ukraine, Géorgie, Arménie, Azerbaïdjan, "
            "Kazakhstan, Kirghizistan, Moldavie, Estonie, Lettonie, Lituanie.\n"
            "❌ *NON éligibles* : *Russie*, *Biélorussie*, *Ouzbékistan*, *Tadjikistan*, *Turkménistan*.\n\n"
            "Contrairement aux catégories EB, *les 7 exigences E-2 sont obligatoires*.\n\n"
            "Répondez « Oui » ou « Non »."
        ),

        "eb1a_questions": [
            "🏆 Avez-vous des prix nationaux ou internationaux majeurs (hors Nobel et similaires) ?",
            "👥 Êtes-vous membre d'une association dont l'adhésion exige des réalisations extraordinaires (selon des experts reconnus) ?",
            "📰 Des articles sur vous ont-ils été publiés dans des médias professionnels ou généraux majeurs ?",
            "⚖️ Avez-vous été juge/évaluateur du travail d'autres spécialistes de votre domaine (jury, peer review, etc.) ?",
            "🔬 Avez-vous des contributions originales d'importance majeure dans votre domaine (inventions, méthodologies, publications citées) ?",
            "📚 Êtes-vous auteur d'articles scientifiques dans des revues à comité de lecture ou médias majeurs ?",
            "🎨 Vos œuvres ont-elles été exposées lors d'expositions artistiques ?",
            "💼 Avez-vous occupé un rôle dirigeant ou critique dans une organisation réputée ?",
            "💰 Votre salaire/rémunération est-il nettement supérieur à la moyenne du secteur ?",
            "🎭 Avez-vous un succès commercial dans les arts du spectacle (recettes, ventes, etc.) ?",
        ],
        "niw_questions": [
            "🇺🇸 Votre activité a-t-elle un mérite substantiel et une importance nationale pour les USA (santé, technologies, économie, culture, défense, etc.) ?",
            "🎯 Êtes-vous bien positionné pour faire avancer cette activité (formation, expérience, progrès, plans, ressources, intérêt d'investisseurs/employeurs) ?",
            "⚖️ Existe-t-il des raisons pour lesquelles l'exigence de PERM labor certification est impraticable (urgence, unicité, votre apport l'emporte) ?",
        ],
        "o1_questions": [
            "🏆 Avez-vous des prix nationaux/internationaux majeurs dans votre domaine ?",
            "👥 Membre d'associations exigeant des réalisations extraordinaires ?",
            "📰 Publications sur vous dans des médias professionnels ou majeurs ?",
            "🎯 Contributions originales (scientifiques, business, sportives) d'importance majeure ?",
            "⚖️ Avez-vous été juge/expert du travail d'autres ?",
            "📚 Auteur d'articles scientifiques dans votre domaine ?",
            "💼 Rôle critique/essentiel dans des organisations réputées ?",
            "💰 Salaire/rémunération élevé par rapport aux pairs ?",
        ],
        "e2_questions": [
            "🌍 Êtes-vous citoyen d'un pays ayant un traité E-2 avec les USA (ex. Ukraine, Géorgie, Arménie, Kazakhstan, Turquie ; *Russie — non*, Biélorussie — non) ?",
            "💵 Avez-vous déjà investi des fonds dans une entreprise aux USA ou engagé irrévocablement (transférés, contrats signés, équipement acheté) ? Les fonds doivent être « at-risk ».",
            "📊 L'investissement est-il substantiel et proportionnel au coût/type d'entreprise (généralement $100–150K+ pour petite entreprise, dépend du secteur) ?",
            "🏢 Est-ce une entreprise réelle et active produisant biens ou services (pas une détention passive d'immobilier ou de titres) ?",
            "👔 Détenez-vous au moins 50 % ou avez-vous le contrôle opérationnel (capacité de « develop and direct » l'entreprise) ?",
            "📈 L'entreprise n'est-elle pas marginale — générant ou pouvant générer un revenu supérieur au minimum vital et/ou créant des emplois/contribution à l'économie US ?",
            "✈️ Êtes-vous prêt à déclarer l'intention de quitter les USA à l'expiration du statut E-2 (nonimmigrant intent) ?",
        ],

        "pricing": (
            "💰 *Tarifs et délais*\n\n"
            "*1. Consultation*\n"
            "$300 (60–90 min) — analyse des critères et stratégie pour votre catégorie. "
            "Crédité sur le total si vous nous mandatez.\n\n"
            "*2. Services juridiques (préparation de la pétition par l'équipe d'avocats)*\n"
            "• *EB-1 (A, C)* ou *EB-2 NIW* : *$15 000* — honoraires pour "
            "évaluation et préparation de I-140 + preuves.\n"
            "• *I-485* (carte verte quand la file le permet) : *$500 par membre de famille*.\n"
            "• Paiements échelonnés au contrat — généralement 2–3 tranches.\n\n"
            "*3. Frais USCIS*\n"
            "• *I-140* : *$715*\n"
            "• Asylum program fee : *$300*\n"
            "• *I-485* : *$1 440*\n"
            "• *Premium Processing* : *$2 805*\n\n"
            "*4. Délais*\n"
            "• I-140 — environ *12–16 mois* en traitement standard.\n\n"
            "_Vérifiez frais et délais actuels sur uscis.gov._"
        ),
    },

    # ────────────────────────────────────────────────────────────────── ht (Haitian Creole)
    "ht": {
        "welcome": (
            "Bonjou! 🇺🇸\n"
            "Mwen se yon asistan IA pou viza Ameriken. Kategori prensipal yo: *EB-1A*, *EB-2 NIW*, *O-1*, *E-2*. "
            "Mwen reponn tou kesyon jeneral sou *azil*. Mwen ka ede ou ak:\n"
            "• kritè kalifikasyon yo\n"
            "• dokiman ki nesesè yo\n"
            "• rezon komen pou refi ak estrateji\n\n"
            "Di m sou sitiyasyon ou oswa poze yon kesyon espesifik.\n\n"
            "⚠️ Enfòmasyon sa a se pou referans sèlman, li pa yon konsèy legal. "
            "Chak ka inik e li mande yon egzamen endividyèl."
        ),
        "language_saved": "✅ Lang mete: *Kreyòl Ayisyen*",
        "menu_header": "Meni prensipal:",
        "context_reset": "Kontèks retabli. Chwazi yon aksyon:",
        "lang_changed": "Chwazi lang ou:",

        "btn_ask": "❓ Poze kesyon sou viza",
        "btn_quiz": "📋 Evalye chans mwen (kesyonè)",
        "btn_case_review": "🆓 Revize ka a gratis",
        "btn_pricing": "💰 Pri ak dele",
        "btn_book": "📞 Pran yon konsiltasyon",
        "btn_back": "⬅️ Tounen nan meni",
        "btn_case_done": "✅ Fini voye",
        "btn_yes": "✅ Wi",
        "btn_no": "❌ Non",
        "btn_lang": "🌐 Chanje lang",

        "btn_quiz_eb1a": "EB-1A (Kapasite Ekstraòdinè)",
        "btn_quiz_niw":  "EB-2 NIW (Enterè Nasyonal)",
        "btn_quiz_o1":   "O-1 (Kapasite Ekstraòdinè)",
        "btn_quiz_e2":   "E-2 (Envestisè pa Trete)",

        "ask_prompt": (
            "Poze kesyon ou sou EB-1A, EB-2 NIW, O-1, E-2 oswa azil. "
            "Mwen reponn dapre règ USCIS yo.\n\n"
            "_Mesaj ki rete jodi a: {left}/{total}_"
        ),
        "quiz_start": "Evalyasyon dapre kritè USCIS yo.\n\nKi kesyonè ou vle fè?",
        "quiz_q_header": "*Kesyon {n} sou {total}:*\n\n{q}",
        "quiz_not_active": "Kesyonè a pa aktif ankò. Chwazi yon aksyon:",
        "in_quiz_warning": (
            "Ou nan yon kesyonè — reponn ak bouton *«✅ Wi»* oswa *«❌ Non»* "
            "anba kesyon an. Pou sòti — /menu."
        ),
        "unknown_quiz": "Kategori kesyonè enkoni.",

        "limit_reached": (
            "Ou rive nan limit 15 mesaj pa jou. "
            "Pou kontinye, mwen rekòmande ou kontakte yon espesyalis — li pral revize ka ou endividyèlman.\n\n"
            "Limit la rekòmanse nan 24 èdtan."
        ),
        "footer_remaining": "\n\n_Rete jodi a: {left}/{total}_",
        "llm_error": "Erè tanporè nan baz konesans lan. Eseye ankò nan yon minit.",

        "lead_prompt": (
            "Pou yon espesyalis kontakte ou, tanpri bay:\n\n"
            "1️⃣ *Non*\n"
            "2️⃣ *Kout deskripsyon sitiyasyon ou* (pwofesyon, viza ki enterese w)\n\n"
            "Voye tout nan yon sèl mesaj."
        ),
        "lead_received": (
            "✅ Mèsi! Demann ou resevwa. "
            "Yon espesyalis ap kontakte w nan jounen travay la."
        ),

        "case_review_info": (
            "🆓 *Revi gratis sou ka ou*\n\n"
            "⚠️ *Enpòtan:* tout sa ou ekri ak tache la a *ap voye bay yon espesyalis an chè ak an zo* "
            "— pa yon asistan IA. P ap gen repons nan bot la — ekspè a ap kontakte w pèsonèlman.\n\n"
            "_Pou poze IA yon kesyon — peze «⬅️ Tounen nan meni» epi chwazi «❓ Poze kesyon sou viza»._\n\n"
            "Dekri sitiyasyon ou (pwofesyon, eksperyans, objektif) epi tache dokiman si ou vle — "
            "CV, diplòm, atik, prim, lèt rekòmandasyon.\n\n"
            "📎 *Ki jan pou tache yon fichye:* peze sou klips bò goch chan antre a → "
            "chwazi «Fichye» oswa «Foto» → voye. PDF, DOCX, JPG, PNG akseptab jiska 2 GB.\n\n"
            "Ou ka voye *plizyè mesaj*. Lè ou fini — peze *«Fini voye»*.\n\n"
            "_Yon espesyalis ap kontakte w nan 1-2 jou travay._"
        ),
        "case_review_forwarded": (
            "✓ Voye bay espesyalis la. Li pral reponn pèsonèlman (pa atravè bot la) "
            "nan 1-2 jou travay.\n\n"
            "Ou ka voye lòt materyèl oswa peze «Fini voye»."
        ),
        "case_review_forward_failed": (
            "⚠️ Pa t kapab voye mesaj sa a bay espesyalis la. "
            "Eseye ankò oswa dekri sitiyasyon an nan «Pran yon konsiltasyon»."
        ),
        "case_review_done": (
            "✅ Mèsi! Yon ekspè ap revize demann ou epi kontakte w nan "
            "1-2 jou travay."
        ),
        "case_button_inactive": "Bouton sa a pa aktif ankò. Chwazi yon aksyon:",
        "booking_file_ok": "✓ Fichye resevwa. Si ou poko voye non ak deskripsyon — voye yo nan yon mesaj.",
        "booking_file_failed": (
            "⚠️ Pa t kapab voye fichye a. Eseye ankò oswa dekri sitiyasyon an an tèks."
        ),
        "attachment_hint": (
            "Pou voye dokiman — chwazi nan meni «🆓 Revize ka a gratis» "
            "oswa «📞 Pran yon konsiltasyon»."
        ),

        "quiz_intro_eb1a": (
            "*EB-1A* — Kapasite Ekstraòdinè. Ou bezwen omwen *3 sou 10* kritè "
            "plis yon analiz Final Merits pozitif.\n\nReponn «Wi» oswa «Non»."
        ),
        "quiz_intro_niw": (
            "*EB-2 NIW* — National Interest Waiver. Tès la soti nan *Matter of Dhanasar* (2016) — "
            "twa eleman obligatwa.\n\nReponn «Wi» oswa «Non»."
        ),
        "quiz_intro_o1": (
            "*O-1A* — viza pou moun ki gen kapasite ekstraòdinè (syans, biznis, espò). "
            "Ou bezwen omwen *3 sou 8* kritè.\n\nReponn «Wi» oswa «Non»."
        ),
        "quiz_intro_e2": (
            "*E-2* — viza pou envestisè ki soti nan peyi ki gen trete komèsyal avèk USA.\n\n"
            "🌍 *Peyi ansyen URSS ak E-2:*\n"
            "✅ *Kalifye*: Ikrèn, Jeòji, Almeni, Azèbayan, "
            "Kazaksan, Kirgistan, Moldavi, Estoni, Letoni, Litwani.\n"
            "❌ *PA kalifye*: *Risi*, *Byelorisi*, *Ouzbekistan*, *Tajikistan*, *Tirkmenistan*.\n\n"
            "Kontrèman ak kategori EB yo, *tout 7 egzijans E-2 yo obligatwa*.\n\n"
            "Reponn «Wi» oswa «Non»."
        ),

        "eb1a_questions": [
            "🏆 Èske ou gen gwo prim nasyonal oswa entènasyonal (apa Nobel ak menm jan an)?",
            "👥 Èske ou manm yon asosyasyon ki mande reyalizasyon ekstraòdinè (selon ekspè rekonèt)?",
            "📰 Èske gen atik sou ou ki pibliye nan gwo medya pwofesyonèl oswa jeneral?",
            "⚖️ Èske ou te jij/revizè travay lòt espesyalis nan domèn ou (jiri, peer review, elatriye)?",
            "🔬 Èske ou gen kontribisyon orijinal enpòtan nan domèn ou (envansyon, metodoloji, piblikasyon ki site)?",
            "📚 Èske ou otè atik syantifik nan jounal ak peer review oswa gwo medya?",
            "🎨 Èske yo te ekspoze travay ou nan ekspozisyon atistik?",
            "💼 Èske ou te okipe yon wòl dirijan oswa kritik nan yon òganizasyon repite?",
            "💰 Èske salè/remunerasyon ou anpil pi wo pase mwayèn nan domèn ou?",
            "🎭 Èske ou gen siksè komèsyal nan atizay pèfòmans (rekòt, vant, elatriye)?",
        ],
        "niw_questions": [
            "🇺🇸 Èske travay ou gen mèrit sibstansyèl ak enpòtans nasyonal pou USA (sante, teknoloji, ekonomi, kilti, defans, elatriye)?",
            "🎯 Èske ou byen pozisyone pou avanse aktivite sa a (edikasyon, eksperyans, pwogrè, plan, resous, enterè envestisè/anplwayè)?",
            "⚖️ Èske gen rezon pou kondisyon PERM labor certification pa pratik (ijans, inisite, kontribisyon ou pi enpòtan pase pwosedi a)?",
        ],
        "o1_questions": [
            "🏆 Èske ou gen gwo prim nasyonal/entènasyonal nan domèn ou?",
            "👥 Manm asosyasyon ki mande reyalizasyon ekstraòdinè?",
            "📰 Piblikasyon sou ou nan medya pwofesyonèl oswa gwo medya?",
            "🎯 Kontribisyon orijinal (syantifik, biznis, espò) ki trè enpòtan?",
            "⚖️ Èske ou te jij/ekspè travay lòt moun?",
            "📚 Otè atik syantifik nan domèn ou?",
            "💼 Wòl kritik/esansyèl nan òganizasyon repite?",
            "💰 Gwo salè/remunerasyon konpare ak kolèg?",
        ],
        "e2_questions": [
            "🌍 Èske ou sitwayen yon peyi ki gen trete E-2 ak USA (egz. Ikrèn, Jeòji, Almeni, Kazaksan, Tiki; *Risi — non*, Byelorisi — non)?",
            "💵 Èske ou deja envesti lajan nan yon biznis nan USA oswa angaje yo san retou (transfere, kontra siyen, ekipman achte)? Lajan an dwe «at-risk».",
            "📊 Èske envestisman an sibstansyèl e pwopòsyonèl ak pri/tip biznis la (jeneralman $100–150K+ pou ti biznis, depann sektè)?",
            "🏢 Èske se yon biznis reyèl k ap fonksyone k ap pwodui byen oswa sèvis (pa posesyon pasif imobilye oswa valè)?",
            "👔 Èske ou posede omwen 50% oswa ou gen kontwòl operasyonèl (kapab «develop and direct» biznis la)?",
            "📈 Èske biznis la pa majinal — li jenere oswa kapab jenere revni pi wo pase minimòm lavi ak/oswa kreye travay/kontribisyon ekonomi USA?",
            "✈️ Èske ou prepare pou deklare entansyon kite USA apre estati E-2 fini (nonimmigrant intent)?",
        ],

        "pricing": (
            "💰 *Pri ak Dele*\n\n"
            "*1. Konsiltasyon*\n"
            "$300 (60–90 min) — analiz kritè ak estrateji pou kategori ou. "
            "Kredite sou total ka a si ou kontinye avèk nou.\n\n"
            "*2. Sèvis legal (preparasyon petisyon pa ekip avoka)*\n"
            "• *EB-1 (A, C)* oswa *EB-2 NIW*: *$15 000* — frè avoka "
            "pou evalyasyon ak preparasyon I-140 + prèv.\n"
            "• *I-485* (green card lè liy lan disponib): *$500 pou chak manm fanmi*.\n"
            "• Peman an etap nan kontra a — anjeneral 2–3 tranch.\n\n"
            "*3. Frè gouvènman USCIS*\n"
            "• *I-140*: *$715*\n"
            "• Asylum program fee: *$300*\n"
            "• *I-485*: *$1,440*\n"
            "• *Premium Processing*: *$2,805*\n\n"
            "*4. Dele*\n"
            "• I-140 — anviwon *12–16 mwa* nan tretman estanda.\n\n"
            "_Verifye frè ak dele aktyèl sou uscis.gov._"
        ),
    },

    # ────────────────────────────────────────────────────────────────── pt
    "pt": {
        "welcome": (
            "Olá! 🇺🇸\n"
            "Sou um assistente de IA para vistos dos EUA. Categorias principais: *EB-1A*, *EB-2 NIW*, *O-1*, *E-2*. "
            "Também respondo a perguntas gerais sobre *asilo*. Posso ajudar com:\n"
            "• critérios de qualificação\n"
            "• requisitos documentais\n"
            "• motivos comuns de negação e estratégias\n\n"
            "Conte-me sua situação ou faça uma pergunta específica.\n\n"
            "⚠️ Informação apenas para referência, não é aconselhamento jurídico. "
            "Cada caso é único e requer análise individual."
        ),
        "language_saved": "✅ Idioma definido: *Português*",
        "menu_header": "Menu principal:",
        "context_reset": "Contexto reiniciado. Escolha uma ação:",
        "lang_changed": "Escolha o seu idioma:",

        "btn_ask": "❓ Perguntar sobre visto",
        "btn_quiz": "📋 Avaliar chances (questionário)",
        "btn_case_review": "🆓 Análise gratuita do caso",
        "btn_pricing": "💰 Preços e prazos",
        "btn_book": "📞 Agendar consulta",
        "btn_back": "⬅️ Ao menu",
        "btn_case_done": "✅ Concluir envio",
        "btn_yes": "✅ Sim",
        "btn_no": "❌ Não",
        "btn_lang": "🌐 Mudar idioma",

        "btn_quiz_eb1a": "EB-1A (Habilidade Extraordinária)",
        "btn_quiz_niw":  "EB-2 NIW (Interesse Nacional)",
        "btn_quiz_o1":   "O-1 (Habilidade Extraordinária)",
        "btn_quiz_e2":   "E-2 (Investidor por Tratado)",

        "ask_prompt": (
            "Faça sua pergunta sobre EB-1A, EB-2 NIW, O-1, E-2 ou asilo. "
            "Respondo com base nas regras do USCIS.\n\n"
            "_Mensagens restantes hoje: {left}/{total}_"
        ),
        "quiz_start": "Avaliação pelos critérios do USCIS.\n\nQual questionário deseja fazer?",
        "quiz_q_header": "*Pergunta {n} de {total}:*\n\n{q}",
        "quiz_not_active": "O questionário não está mais ativo. Escolha uma ação:",
        "in_quiz_warning": (
            "Você está num questionário — responda com os botões *«✅ Sim»* ou *«❌ Não»* "
            "abaixo da pergunta. Para sair — /menu."
        ),
        "unknown_quiz": "Categoria de questionário desconhecida.",

        "limit_reached": (
            "Você atingiu o limite diário de 15 mensagens. "
            "Para continuar, recomendo contactar um especialista — ele analisará seu caso individualmente.\n\n"
            "O limite é reiniciado em 24 horas."
        ),
        "footer_remaining": "\n\n_Restantes hoje: {left}/{total}_",
        "llm_error": "Erro temporário ao consultar a base de conhecimento. Tente novamente em um minuto.",

        "lead_prompt": (
            "Para um especialista entrar em contato, por favor informe:\n\n"
            "1️⃣ *Nome*\n"
            "2️⃣ *Breve descrição da sua situação* (profissão, visto de interesse)\n\n"
            "Envie tudo em uma mensagem."
        ),
        "lead_received": (
            "✅ Obrigado! Sua solicitação foi recebida. "
            "Um especialista entrará em contato durante o dia útil."
        ),

        "case_review_info": (
            "🆓 *Análise gratuita do seu caso*\n\n"
            "⚠️ *Importante:* tudo que você escrever e anexar aqui *será encaminhado a um especialista humano* "
            "— não a um assistente de IA. Não haverá resposta no bot — o especialista entrará em contato pessoalmente.\n\n"
            "_Para perguntar à IA — toque em «⬅️ Ao menu» e escolha «❓ Perguntar sobre visto»._\n\n"
            "Descreva sua situação (profissão, experiência, objetivos) e anexe documentos se desejar — "
            "CV, diplomas, artigos, prêmios, cartas de recomendação.\n\n"
            "📎 *Como anexar arquivo:* toque no clipe à esquerda do campo de texto → "
            "escolha «Arquivo» ou «Foto» → envie. PDF, DOCX, JPG, PNG e outros até 2 GB por arquivo.\n\n"
            "Pode enviar *várias mensagens*. Ao terminar — toque em *«Concluir envio»*.\n\n"
            "_Um especialista entrará em contato em 1-2 dias úteis._"
        ),
        "case_review_forwarded": (
            "✓ Encaminhado ao especialista. Ele responderá pessoalmente (não pelo bot) "
            "em 1-2 dias úteis.\n\n"
            "Pode enviar mais materiais ou tocar em «Concluir envio»."
        ),
        "case_review_forward_failed": (
            "⚠️ Não foi possível encaminhar esta mensagem. "
            "Tente novamente ou descreva a situação em «Agendar consulta»."
        ),
        "case_review_done": (
            "✅ Obrigado! Um especialista analisará seu pedido e entrará em contato "
            "em 1-2 dias úteis."
        ),
        "case_button_inactive": "Este botão não está mais ativo. Escolha uma ação:",
        "booking_file_ok": "✓ Arquivo recebido. Se ainda não enviou nome e descrição — envie numa mensagem.",
        "booking_file_failed": (
            "⚠️ Não foi possível encaminhar o arquivo. Tente novamente ou descreva por texto."
        ),
        "attachment_hint": (
            "Para enviar documentos — escolha no menu «🆓 Análise gratuita do caso» "
            "ou «📞 Agendar consulta»."
        ),

        "quiz_intro_eb1a": (
            "*EB-1A* — Habilidade Extraordinária. São necessários pelo menos *3 de 10* critérios "
            "mais análise Final Merits positiva.\n\nResponda «Sim» ou «Não»."
        ),
        "quiz_intro_niw": (
            "*EB-2 NIW* — National Interest Waiver. Teste do caso *Matter of Dhanasar* (2016) — "
            "três elementos obrigatórios.\n\nResponda «Sim» ou «Não»."
        ),
        "quiz_intro_o1": (
            "*O-1A* — visto para pessoas com habilidades extraordinárias (ciência, negócios, esportes). "
            "São necessários pelo menos *3 de 8* critérios.\n\nResponda «Sim» ou «Não»."
        ),
        "quiz_intro_e2": (
            "*E-2* — visto para investidores de países com tratado comercial com os EUA.\n\n"
            "🌍 *Países ex-URSS e E-2:*\n"
            "✅ *Qualificam*: Ucrânia, Geórgia, Armênia, Azerbaijão, "
            "Cazaquistão, Quirguistão, Moldávia, Estônia, Letônia, Lituânia.\n"
            "❌ *NÃO qualificam*: *Rússia*, *Belarus*, *Uzbequistão*, *Tajiquistão*, *Turcomenistão*.\n\n"
            "Ao contrário das categorias EB, *os 7 requisitos do E-2 são obrigatórios*.\n\n"
            "Responda «Sim» ou «Não»."
        ),

        "eb1a_questions": [
            "🏆 Você tem grandes prêmios nacionais ou internacionais (exceto Nobel e similares)?",
            "👥 Você é membro de uma associação cuja filiação exige conquistas extraordinárias (segundo especialistas reconhecidos)?",
            "📰 Foram publicados materiais sobre você em grandes mídias profissionais ou gerais?",
            "⚖️ Você atuou como juiz/revisor do trabalho de outros na sua área (júri, peer review, etc.)?",
            "🔬 Tem contribuições originais de grande importância na sua área (invenções, metodologias, publicações citadas)?",
            "📚 É autor de artigos científicos em revistas revisadas por pares ou grandes mídias?",
            "🎨 Seus trabalhos foram exibidos em exposições artísticas?",
            "💼 Ocupou papel de liderança ou crítico em organização renomada?",
            "💰 Seu salário/honorário é substancialmente superior à média da área?",
            "🎭 Tem sucesso comercial nas artes performáticas (bilheteria, vendas, etc.)?",
        ],
        "niw_questions": [
            "🇺🇸 Sua atividade tem mérito substancial e importância nacional para os EUA (saúde, tecnologia, economia, cultura, defesa, etc.)?",
            "🎯 Está bem posicionado para avançar essa atividade (educação, experiência, progresso, planos, recursos, interesse de investidores/empregadores)?",
            "⚖️ Existem razões pelas quais o requisito de PERM labor certification é impraticável (urgência, unicidade, sua contribuição supera o processo)?",
        ],
        "o1_questions": [
            "🏆 Tem grandes prêmios nacionais/internacionais na sua área?",
            "👥 Membro de associações que exigem conquistas extraordinárias?",
            "📰 Publicações sobre você em mídias profissionais ou grandes?",
            "🎯 Contribuições originais (científicas, empresariais, esportivas) de grande importância?",
            "⚖️ Atuou como juiz/especialista do trabalho de outros?",
            "📚 Autoria de artigos científicos na sua área?",
            "💼 Papel crítico/essencial em organizações renomadas?",
            "💰 Alto salário/honorários comparado com pares?",
        ],
        "e2_questions": [
            "🌍 É cidadão de país com tratado E-2 com os EUA (ex. Ucrânia, Geórgia, Armênia, Cazaquistão, Turquia; *Rússia — não*, Belarus — não)?",
            "💵 Já investiu fundos num negócio nos EUA ou comprometeu-os irrevogavelmente (transferidos, contratos assinados, equipamento comprado)? Fundos devem estar «at-risk».",
            "📊 O investimento é substancial e proporcional ao custo/tipo de negócio (tipicamente $100–150K+ para pequeno negócio, depende do setor)?",
            "🏢 É um negócio real e ativo produzindo bens ou serviços (não posse passiva de imóveis ou valores)?",
            "👔 Detém pelo menos 50% ou tem controle operacional (capaz de «develop and direct» a empresa)?",
            "📈 O negócio não é marginal — gerando ou capaz de gerar renda acima do mínimo de subsistência e/ou criando empregos/contribuição para a economia dos EUA?",
            "✈️ Está preparado para declarar intenção de sair dos EUA ao fim do status E-2 (nonimmigrant intent)?",
        ],

        "pricing": (
            "💰 *Preços e Prazos*\n\n"
            "*1. Consulta*\n"
            "$300 (60–90 min) — análise de critérios e estratégia para sua categoria. "
            "Creditado no total do caso se prosseguir conosco.\n\n"
            "*2. Serviços jurídicos (preparação da petição pela equipe de advogados)*\n"
            "• *EB-1 (A, C)* ou *EB-2 NIW*: *$15 000* — honorários "
            "por avaliação e preparação de I-140 + evidências.\n"
            "• *I-485* (green card quando houver vaga): *$500 por membro da família*.\n"
            "• Pagamentos escalonados no contrato — normalmente 2–3 tranches.\n\n"
            "*3. Taxas do USCIS*\n"
            "• *I-140*: *$715*\n"
            "• Asylum program fee: *$300*\n"
            "• *I-485*: *$1,440*\n"
            "• *Premium Processing*: *$2,805*\n\n"
            "*4. Prazos*\n"
            "• I-140 — cerca de *12–16 meses* no processamento padrão.\n\n"
            "_Confirme taxas e prazos atuais em uscis.gov._"
        ),
    },

    # ────────────────────────────────────────────────────────────────── hi (Hindi)
    "hi": {
        "welcome": (
            "नमस्ते! 🇺🇸\n"
            "मैं अमेरिकी वीज़ा के लिए एक AI सहायक हूँ। मुख्य श्रेणियाँ: *EB-1A*, *EB-2 NIW*, *O-1*, *E-2*। "
            "मैं *शरण (asylum)* पर सामान्य प्रश्नों का भी उत्तर देता हूँ। मैं सहायता कर सकता हूँ:\n"
            "• योग्यता मानदंडों में\n"
            "• दस्तावेज़ आवश्यकताओं में\n"
            "• सामान्य अस्वीकृति कारणों और रणनीतियों में\n\n"
            "अपनी स्थिति बताइए या कोई विशिष्ट प्रश्न पूछिए।\n\n"
            "⚠️ यह जानकारी केवल संदर्भ के लिए है, कानूनी सलाह नहीं। "
            "प्रत्येक मामला अनोखा है और व्यक्तिगत समीक्षा की आवश्यकता होती है।"
        ),
        "language_saved": "✅ भाषा सेट की गई: *हिन्दी*",
        "menu_header": "मुख्य मेनू:",
        "context_reset": "संदर्भ रीसेट हुआ। क्रिया चुनें:",
        "lang_changed": "अपनी भाषा चुनें:",

        "btn_ask": "❓ वीज़ा पर प्रश्न पूछें",
        "btn_quiz": "📋 संभावनाओं का मूल्यांकन",
        "btn_case_review": "🆓 निःशुल्क केस समीक्षा",
        "btn_pricing": "💰 शुल्क और समयसीमा",
        "btn_book": "📞 परामर्श बुक करें",
        "btn_back": "⬅️ मेनू पर",
        "btn_case_done": "✅ भेजना समाप्त करें",
        "btn_yes": "✅ हाँ",
        "btn_no": "❌ नहीं",
        "btn_lang": "🌐 भाषा बदलें",

        "btn_quiz_eb1a": "EB-1A (असाधारण योग्यता)",
        "btn_quiz_niw":  "EB-2 NIW (राष्ट्रीय हित)",
        "btn_quiz_o1":   "O-1 (असाधारण योग्यता)",
        "btn_quiz_e2":   "E-2 (संधि निवेशक)",

        "ask_prompt": (
            "EB-1A, EB-2 NIW, O-1, E-2 या शरण के बारे में अपना प्रश्न पूछें। "
            "मैं USCIS नियमों के आधार पर उत्तर देता हूँ।\n\n"
            "_आज शेष संदेश: {left}/{total}_"
        ),
        "quiz_start": "USCIS मानदंडों पर मूल्यांकन।\n\nकौन-सा प्रश्नोत्तर करना चाहेंगे?",
        "quiz_q_header": "*प्रश्न {n} / {total}:*\n\n{q}",
        "quiz_not_active": "प्रश्नोत्तर अब सक्रिय नहीं है। क्रिया चुनें:",
        "in_quiz_warning": (
            "आप अभी प्रश्नोत्तर में हैं — ऊपर दिए गए प्रश्न के नीचे "
            "*«✅ हाँ»* या *«❌ नहीं»* बटन से उत्तर दें। बाहर निकलने के लिए — /menu।"
        ),
        "unknown_quiz": "अज्ञात प्रश्नोत्तर श्रेणी।",

        "limit_reached": (
            "आपने दैनिक 15 संदेशों की सीमा पूरी कर ली है। "
            "जारी रखने के लिए किसी विशेषज्ञ से संपर्क करें — वे आपके केस की व्यक्तिगत समीक्षा करेंगे।\n\n"
            "सीमा 24 घंटे में रीसेट होगी।"
        ),
        "footer_remaining": "\n\n_आज शेष: {left}/{total}_",
        "llm_error": "ज्ञान-आधार से अस्थायी त्रुटि। एक मिनट बाद पुनः प्रयास करें।",

        "lead_prompt": (
            "विशेषज्ञ से संपर्क के लिए कृपया दें:\n\n"
            "1️⃣ *नाम*\n"
            "2️⃣ *अपनी स्थिति का संक्षिप्त विवरण* (पेशा, वीज़ा)\n\n"
            "एक ही संदेश में भेजें।"
        ),
        "lead_received": (
            "✅ धन्यवाद! आपका अनुरोध प्राप्त हुआ। "
            "विशेषज्ञ कार्य-दिवस में आपसे संपर्क करेंगे।"
        ),

        "case_review_info": (
            "🆓 *आपके केस की निःशुल्क समीक्षा*\n\n"
            "⚠️ *महत्वपूर्ण:* यहाँ आप जो भी लिखेंगे और संलग्न करेंगे वह *सीधे एक मानव विशेषज्ञ को भेजा जाता है* "
            "— AI सहायक को नहीं। बॉट में कोई उत्तर नहीं आएगा — विशेषज्ञ स्वयं संपर्क करेंगे।\n\n"
            "_AI से प्रश्न पूछने के लिए «⬅️ मेनू पर» दबाएँ और «❓ वीज़ा पर प्रश्न पूछें» चुनें।_\n\n"
            "अपनी स्थिति का वर्णन करें (पेशा, अनुभव, लक्ष्य) और दस्तावेज़ संलग्न करें यदि चाहें — "
            "CV, डिग्री, लेख, पुरस्कार, अनुशंसा पत्र।\n\n"
            "📎 *फ़ाइल कैसे संलग्न करें:* संदेश बॉक्स के बाईं ओर क्लिप आइकन पर टैप करें → "
            "«File» या «Photo» चुनें → भेजें। PDF, DOCX, JPG, PNG आदि प्रति फ़ाइल 2 GB तक।\n\n"
            "*कई संदेश* भेज सकते हैं। समाप्त होने पर *«भेजना समाप्त करें»* दबाएँ।\n\n"
            "_विशेषज्ञ 1-2 कार्य-दिवसों में संपर्क करेंगे।_"
        ),
        "case_review_forwarded": (
            "✓ विशेषज्ञ को भेज दिया गया। वे व्यक्तिगत रूप से (बॉट से नहीं) "
            "1-2 कार्य-दिवसों में उत्तर देंगे।\n\n"
            "और सामग्री भेज सकते हैं या «भेजना समाप्त करें» दबाएँ।"
        ),
        "case_review_forward_failed": (
            "⚠️ यह संदेश विशेषज्ञ को भेजा नहीं जा सका। "
            "पुनः प्रयास करें या «परामर्श बुक करें» में टेक्स्ट द्वारा विवरण दें।"
        ),
        "case_review_done": (
            "✅ धन्यवाद! विशेषज्ञ आपके अनुरोध की समीक्षा करेंगे और "
            "1-2 कार्य-दिवसों में संपर्क करेंगे।"
        ),
        "case_button_inactive": "यह बटन अब सक्रिय नहीं है। क्रिया चुनें:",
        "booking_file_ok": "✓ फ़ाइल प्राप्त हुई। यदि नाम और विवरण अभी तक नहीं भेजे — एक संदेश में भेजें।",
        "booking_file_failed": (
            "⚠️ फ़ाइल भेजी नहीं जा सकी। पुनः प्रयास करें या टेक्स्ट में विवरण दें।"
        ),
        "attachment_hint": (
            "दस्तावेज़ भेजने के लिए मेनू से «🆓 निःशुल्क केस समीक्षा» "
            "या «📞 परामर्श बुक करें» चुनें।"
        ),

        "quiz_intro_eb1a": (
            "*EB-1A* — असाधारण योग्यता। कम से कम *10 में से 3* मानदंड "
            "और सकारात्मक Final Merits विश्लेषण आवश्यक।\n\n«हाँ» या «नहीं» में उत्तर दें।"
        ),
        "quiz_intro_niw": (
            "*EB-2 NIW* — National Interest Waiver। *Matter of Dhanasar* (2016) केस का परीक्षण — "
            "तीन अनिवार्य तत्व।\n\n«हाँ» या «नहीं» में उत्तर दें।"
        ),
        "quiz_intro_o1": (
            "*O-1A* — असाधारण योग्यता वाले व्यक्तियों के लिए वीज़ा (विज्ञान, व्यवसाय, खेल)। "
            "कम से कम *8 में से 3* मानदंड आवश्यक।\n\n«हाँ» या «नहीं» में उत्तर दें।"
        ),
        "quiz_intro_e2": (
            "*E-2* — अमेरिका के साथ व्यापार संधि वाले देशों के निवेशकों के लिए वीज़ा।\n\n"
            "🌍 *पूर्व USSR देश और E-2:*\n"
            "✅ *पात्र*: यूक्रेन, जॉर्जिया, आर्मेनिया, अज़रबैजान, "
            "कज़ाकिस्तान, किर्गिस्तान, मोल्दोवा, एस्टोनिया, लातविया, लिथुआनिया।\n"
            "❌ *अपात्र*: *रूस*, *बेलारूस*, *उज़बेकिस्तान*, *ताजिकिस्तान*, *तुर्कमेनिस्तान*।\n\n"
            "EB श्रेणियों के विपरीत, *E-2 की सभी 7 आवश्यकताएँ अनिवार्य हैं*।\n\n"
            "«हाँ» या «नहीं» में उत्तर दें।"
        ),

        "eb1a_questions": [
            "🏆 क्या आपके पास बड़े राष्ट्रीय या अंतर्राष्ट्रीय पुरस्कार हैं (नोबेल और समकक्ष को छोड़कर)?",
            "👥 क्या आप ऐसे संघ के सदस्य हैं जिसकी सदस्यता के लिए असाधारण उपलब्धियाँ आवश्यक हैं (मान्यता प्राप्त विशेषज्ञों के अनुसार)?",
            "📰 क्या आप पर बड़े पेशेवर या सामान्य मीडिया में सामग्री प्रकाशित हुई है?",
            "⚖️ क्या आपने अपने क्षेत्र में अन्य विशेषज्ञों के काम के न्यायाधीश/समीक्षक के रूप में कार्य किया है (जूरी, peer review आदि)?",
            "🔬 क्या आपके क्षेत्र में बड़े महत्व के मौलिक योगदान हैं (आविष्कार, पद्धतियाँ, उद्धृत प्रकाशन)?",
            "📚 क्या आप peer-reviewed जर्नलों या बड़े मीडिया में शोध लेखों के लेखक हैं?",
            "🎨 क्या आपके काम कला प्रदर्शनियों में प्रदर्शित हुए हैं?",
            "💼 क्या आपने प्रतिष्ठित संगठन में अग्रणी/महत्वपूर्ण भूमिका निभाई है?",
            "💰 क्या आपका वेतन/मेहनताना क्षेत्र के औसत से काफी अधिक है?",
            "🎭 क्या प्रदर्शन कला में आपको व्यावसायिक सफलता मिली है (बॉक्स ऑफिस, बिक्री आदि)?",
        ],
        "niw_questions": [
            "🇺🇸 क्या आपका कार्य अमेरिका के लिए महत्वपूर्ण और राष्ट्रीय महत्व का है (स्वास्थ्य, प्रौद्योगिकी, अर्थव्यवस्था, संस्कृति, रक्षा आदि)?",
            "🎯 क्या आप इसे आगे बढ़ाने के लिए अच्छी स्थिति में हैं (शिक्षा, अनुभव, प्रगति, योजनाएँ, संसाधन, निवेशकों/नियोक्ताओं की रुचि)?",
            "⚖️ क्या ऐसे कारण हैं जिनसे PERM labor certification आवश्यकता अव्यावहारिक है (तात्कालिकता, विशिष्टता, आपका योगदान प्रक्रिया से अधिक महत्वपूर्ण)?",
        ],
        "o1_questions": [
            "🏆 क्या आपके क्षेत्र में बड़े राष्ट्रीय/अंतर्राष्ट्रीय पुरस्कार हैं?",
            "👥 क्या असाधारण उपलब्धियाँ माँगने वाले संघों की सदस्यता है?",
            "📰 क्या पेशेवर या बड़े मीडिया में आप पर प्रकाशन हैं?",
            "🎯 क्या क्षेत्र में बड़े महत्व के मौलिक योगदान (वैज्ञानिक, व्यवसाय, खेल) हैं?",
            "⚖️ क्या आपने अन्य लोगों के काम के न्यायाधीश/विशेषज्ञ की भूमिका निभाई है?",
            "📚 क्या आपके क्षेत्र में शोध लेखों का लेखन है?",
            "💼 क्या प्रतिष्ठित संगठनों में महत्वपूर्ण भूमिका है?",
            "💰 क्या सहकर्मियों की तुलना में उच्च वेतन/मेहनताना है?",
        ],
        "e2_questions": [
            "🌍 क्या आप अमेरिका के साथ E-2 संधि वाले देश के नागरिक हैं (जैसे यूक्रेन, जॉर्जिया, आर्मेनिया, कज़ाकिस्तान, तुर्की; *रूस — नहीं*, बेलारूस — नहीं)?",
            "💵 क्या आपने अमेरिका में व्यवसाय में निवेश किया है या अपरिवर्तनीय रूप से प्रतिबद्ध किया है (स्थानांतरित, अनुबंध हस्ताक्षरित, उपकरण खरीदा)? फंड «at-risk» होने चाहिए।",
            "📊 क्या निवेश पर्याप्त और व्यवसाय की लागत/प्रकार के अनुरूप है (छोटे व्यवसाय के लिए आमतौर पर $100–150K+, क्षेत्र पर निर्भर)?",
            "🏢 क्या यह वस्तुएँ या सेवाएँ उत्पादित करने वाला वास्तविक संचालित व्यवसाय है (निष्क्रिय रियल-एस्टेट/प्रतिभूति धारण नहीं)?",
            "👔 क्या आपके पास कम से कम 50% स्वामित्व या परिचालन नियंत्रण है («develop and direct» करने में सक्षम)?",
            "📈 क्या व्यवसाय marginal नहीं है — न्यूनतम निर्वाह से अधिक आय उत्पन्न कर रहा/कर सकता है और/या नौकरियाँ/अमेरिकी अर्थव्यवस्था में योगदान दे रहा है?",
            "✈️ क्या आप E-2 स्थिति समाप्त होने पर अमेरिका छोड़ने का इरादा घोषित करने को तैयार हैं (nonimmigrant intent)?",
        ],

        "pricing": (
            "💰 *शुल्क और समयसीमा*\n\n"
            "*1. परामर्श*\n"
            "$300 (60–90 मिनट) — आपकी श्रेणी के लिए मानदंड विश्लेषण और रणनीति। "
            "यदि हमारे साथ आगे बढ़ते हैं, तो केस शुल्क में जमा।\n\n"
            "*2. कानूनी सेवाएँ (वकील टीम द्वारा याचिका तैयारी)*\n"
            "• *EB-1 (A, C)* या *EB-2 NIW*: *$15 000* — I-140 + evidence के "
            "मूल्यांकन और तैयारी के लिए attorney fees।\n"
            "• *I-485* (कतार उपलब्ध होने पर green card): *$500 प्रति परिवार सदस्य*।\n"
            "• भुगतान अनुबंध में चरणबद्ध — आमतौर पर 2–3 किस्तें।\n\n"
            "*3. USCIS सरकारी शुल्क*\n"
            "• *I-140*: *$715*\n"
            "• Asylum program fee: *$300*\n"
            "• *I-485*: *$1,440*\n"
            "• *Premium Processing*: *$2,805*\n\n"
            "*4. समयसीमा*\n"
            "• I-140 — मानक प्रोसेसिंग में लगभग *12–16 महीने*।\n\n"
            "_वर्तमान शुल्क और समयसीमा uscis.gov पर सत्यापित करें।_"
        ),
    },

}


def t(key: str, lang: str) -> object:
    """Look up a translation string; fall back to English, then to key."""
    lang = lang if lang in T else "en"
    val = T[lang].get(key)
    if val is None:
        val = T["en"].get(key, key)
    return val


def normalize_lang(lang: str | None) -> str:
    """Return a valid language code; default to DEFAULT_LANG if unknown."""
    if lang and lang in LANG_CODES:
        return lang
    return DEFAULT_LANG

