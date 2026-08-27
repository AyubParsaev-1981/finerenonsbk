"""
Telegram Bot тугмалари ва клавиатуралари (Inline ва Reply).
"""

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Асосий меню клавиатураси."""
    kb = [
        [
            KeyboardButton(text="🩺 Тўлиқ текширув (СБК даражаси + КФТ + АКН)")
        ],
        [
            KeyboardButton(text="⚡ КФТ ҳисоблаш (Креатинин, ёш, вазн)"),
            KeyboardButton(text="🧪 АКН ҳисоблаш (Альбумин/Креатинин)")
        ],
        [
            KeyboardButton(text="📊 KDIGO СБК жадвали"),
            KeyboardButton(text="ℹ️ Бот ҳақида / Қўлланма")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        is_persistent=True
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Ҳисоблашни бекор қилиш тугмаси."""
    kb = [
        [KeyboardButton(text="❌ Бекор қилиш / Бош меню")]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True
    )


def get_gender_inline_keyboard(prefix: str = "full") -> InlineKeyboardMarkup:
    """Жинсни танлаш учун Inline тугмалар."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👨 Эркак", callback_data=f"{prefix}_gender:male"),
                InlineKeyboardButton(text="👩 Аёл", callback_data=f"{prefix}_gender:female"),
            ],
            [
                InlineKeyboardButton(text="❌ Бекор қилиш", callback_data="cancel_calc")
            ]
        ]
    )


def get_blood_creatinine_unit_keyboard(prefix: str = "full") -> InlineKeyboardMarkup:
    """Қондаги креатинин бирлигини танлаш."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="мкмоль/л (µmol/L)", callback_data=f"{prefix}_bcr_unit:umol_l"),
                InlineKeyboardButton(text="мг/дл (mg/dL)", callback_data=f"{prefix}_bcr_unit:mg_dl"),
            ],
            [
                InlineKeyboardButton(text="❌ Бекор қилиш", callback_data="cancel_calc")
            ]
        ]
    )


def get_urine_albumin_unit_keyboard(prefix: str = "full") -> InlineKeyboardMarkup:
    """Сийдикдаги альбумин бирлигини танлаш."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="мг/л (mg/L)", callback_data=f"{prefix}_ualb_unit:mg_l"),
                InlineKeyboardButton(text="мг/дл (mg/dL)", callback_data=f"{prefix}_ualb_unit:mg_dl"),
            ],
            [
                InlineKeyboardButton(text="❌ Бекор қилиш", callback_data="cancel_calc")
            ]
        ]
    )


def get_urine_creatinine_unit_keyboard(prefix: str = "full") -> InlineKeyboardMarkup:
    """Сийдикдаги креатинин бирлигини танлаш."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="г/л (g/L)", callback_data=f"{prefix}_ucr_unit:g_l"),
                InlineKeyboardButton(text="ммоль/л (mmol/L)", callback_data=f"{prefix}_ucr_unit:mmol_l"),
                InlineKeyboardButton(text="мг/дл (mg/dL)", callback_data=f"{prefix}_ucr_unit:mg_dl"),
            ],
            [
                InlineKeyboardButton(text="❌ Бекор қилиш", callback_data="cancel_calc")
            ]
        ]
    )


def get_recalc_inline_keyboard(action_type: str = "full") -> InlineKeyboardMarkup:
    """Қайта ҳисоблаш тугмаси."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔄 Қайта ҳисоблаш", callback_data=f"restart_{action_type}"),
                InlineKeyboardButton(text="🏠 Бош меню", callback_data="goto_main_menu")
            ]
        ]
    )
