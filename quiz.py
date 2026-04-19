# -*- coding: utf-8 -*-
"""Qualification quizzes for EB-1A / EB-2 NIW / O-1 / E-2."""
from prompts import (
    EB1A_QUESTIONS, NIW_QUESTIONS, O1_QUESTIONS, E2_QUESTIONS,
    QUIZ_EB1A_INTRO, QUIZ_NIW_INTRO, QUIZ_O1_INTRO, QUIZ_E2_INTRO,
)

QUIZZES = {
    "eb1a": {"intro": QUIZ_EB1A_INTRO, "questions": EB1A_QUESTIONS, "needed": 3, "total": 10},
    "niw":  {"intro": QUIZ_NIW_INTRO,  "questions": NIW_QUESTIONS,  "needed": 3, "total": 3},
    "o1":   {"intro": QUIZ_O1_INTRO,   "questions": O1_QUESTIONS,   "needed": 3, "total": 8},
    "e2":   {"intro": QUIZ_E2_INTRO,   "questions": E2_QUESTIONS,   "needed": 7, "total": 7},
}

def get_quiz(kind: str):
    return QUIZZES.get(kind)

def summarize(kind: str, answers: list[bool]) -> tuple[str, bool]:
    """
    Returns (summary_text, qualifies_flag).
    qualifies_flag=True means the applicant meets the threshold.
    """
    q = QUIZZES[kind]
    yes = sum(answers)

    if kind == "eb1a":
        qualifies = yes >= 3
        verdict = (
            f"✅ *Вы соответствуете {yes} из 10 критериев.* "
            f"Это превышает минимум в 3 критерия USCIS (8 CFR §204.5(h)(3)). "
            f"Это необходимое, но *не достаточное* условие — ключевую роль "
            f"играет финальный анализ *Kazarian two-step*. "
            f"Рекомендую запросить консультацию для подготовки стратегии кейса."
            if qualifies else
            f"⚠️ *Вы соответствуете {yes} из 10 критериев.* "
            f"Минимум для EB-1A — 3 критерия. Возможно, стоит рассмотреть *EB-2 NIW* "
            f"или *O-1* как альтернативы. Специалист поможет подобрать оптимальный путь."
        )
    elif kind == "niw":
        qualifies = yes == 3
        verdict = (
            "✅ *Все три элемента теста Dhanasar выполнены.* "
            "Это хорошая стартовая позиция для EB-2 NIW. "
            "Следующий шаг — документальное подтверждение каждого элемента "
            "и подготовка петиции I-140."
            if qualifies else
            f"⚠️ *Вы ответили «Да» на {yes} из 3 элементов теста Dhanasar.* "
            "Для NIW требуются *все три*. Рекомендую детальную консультацию — "
            "возможно, элементы выполнены, но их нужно правильно сформулировать."
        )
    elif kind == "o1":
        qualifies = yes >= 3
        verdict = (
            f"✅ *Вы соответствуете {yes} из 8 критериев O-1A.* "
            "Минимум — 3. Также потребуются письма от работодателя и спонсора (consulting letter "
            "от профильной организации, peer group)."
            if qualifies else
            f"⚠️ *Вы соответствуете {yes} из 8 критериев.* "
            "Минимум — 3. Возможно, недостающие критерии можно выстроить — "
            "обсудим на консультации."
        )
    else:  # e2
        qualifies = yes == 7
        verdict = (
            "✅ *Все 7 требований E-2 выполнены.* "
            "Это хорошая стартовая позиция. Следующий шаг — подготовка инвестиционного плана "
            "(business plan на 5 лет), документальное подтверждение источника средств "
            "и проработка «at-risk» инвестиций. Рекомендую консультацию для стратегии кейса."
            if qualifies else
            f"⚠️ *Выполнено {yes} из 7 требований E-2.* "
            "Для этой визы нужны *все 7* — каждое является обязательным по правилам USCIS и Госдепа. "
            "Рекомендую консультацию: часть требований можно выстроить (например, реструктурировать "
            "собственность или увеличить инвестицию), но гражданство договорной страны — жёсткое условие."
        )

    return verdict, qualifies
