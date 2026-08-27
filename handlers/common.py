"""
Умумий буйруқлар ва меню бошқаруви: /start, /help, /cancel, маълумотномалар.
"""

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import settings
from database import db
from keyboards import get_main_menu_keyboard

common_router = Router()


def check_is_admin(user_id: int) -> bool:
    if not settings.admin_ids:
        return True
    return user_id in settings.admin_ids


@common_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """/start буйруғига жавоб ва фойдаланувчини базага ёзиш."""
    await state.clear()
    
    # Фойдаланувчини маълумотлар базасига қўшиш/янгилаш
    if message.from_user:
        await db.add_or_update_user(
            user_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )

    is_admin = check_is_admin(message.from_user.id if message.from_user else 0)

    welcome_text = (
        "👋 **Ассалому алайкум!**\n\n"
        "Ушбу ихтисослаштирилган тиббий бот қуйидагиларни ҳисоблаш ва баҳолашга ёрдам беради:\n\n"
        "🔹 **Коптокчалар фильтрацияси тезлиги (КФТ / GFR)**:\n"
        "   — Кокрофт-Голт (Cockcroft-Gault) клиренси (ёш, вазн, креатинин, жинс асосида)\n"
        "   — CKD-EPI (2021) eGFR формуласи\n"
        "🔹 **Сийдикдаги Альбумин/Креатинин нисбати (АКН / ACR)**:\n"
        "   — Микроальбуминурия ва Макроальбуминурияни аниқлаш (A1, A2, A3)\n"
        "🔹 **Сурункали буйрак касаллиги (СБК / ХБП) KDIGO таснифи**:\n"
        "   — Касаллик босқичи (G1–G5 ва A1–A3) ва асоратлар хавф даражаси\n\n"
        "👇 _Керакли бўлимни қуйидаги тугмалардан танланг:_"
    )
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(is_admin=is_admin),
        parse_mode="Markdown"
    )


@common_router.message(Command("help"))
@common_router.message(F.text == "ℹ️ Бот ҳақида / Қўлланма")
async def cmd_help(message: Message):
    """Қўлланма ва бот ҳақида маълумот."""
    if message.from_user:
        await db.add_or_update_user(message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)

    is_admin = check_is_admin(message.from_user.id if message.from_user else 0)
    help_text = (
        "📖 **Ботдан фойдаланиш қўлланмаси**\n\n"
        "1️⃣ **Тўлиқ текширув**: Беморнинг ёши, вазни, жинси, қондаги креатинин миқдори "
        "ҳамда сийдикдаги альбумин ва креатинин натижалари киритилади. Бот KDIGO матрицаси "
        "бўйича тўлиқ босқич, хавф гуруҳи ва клиник тавсияларни беради.\n\n"
        "2️⃣ **КФТ ҳисоблаш**: Қондаги креатинин, ёш ва вазндан келиб чиқиб КФТ (Cockcroft-Gault & CKD-EPI) ҳисобланади.\n\n"
        "3️⃣ **АКН ҳисоблаш**: Сийдикдаги альбумин ва креатинин нисбати (мг/г ва мг/ммоль) ҳисобланади.\n\n"
        "⚠️ **Муҳим эслатма**: Ушбу бот клиник қарор қабул қилишда шифокорларга ва беморларга кўмакчи "
        "сифатида яратилган бўлиб, расмий ташхис ўрнини босмайди. Якуний хулоса учун мутахассис (нефролог/терапевт) билан маслаҳатлашинг!"
    )
    await message.answer(help_text, reply_markup=get_main_menu_keyboard(is_admin=is_admin), parse_mode="Markdown")


@common_router.message(F.text == "📊 KDIGO СБК жадвали")
async def show_kdigo_table(message: Message):
    """KDIGO СБК таснифи ва хавф матрицаси жадвали."""
    if message.from_user:
        await db.add_or_update_user(message.from_user.id, message.from_user.username, message.from_user.first_name, message.from_user.last_name)

    is_admin = check_is_admin(message.from_user.id if message.from_user else 0)
    table_text = (
        "📊 **KDIGO бўйича СБК (ХБП) Хавф Матрицаси**\n\n"
        "**КФТ босқичлари (мл/мин/1.73м²):**\n"
        "• **G1** (≥ 90): Нормал ёки юқори\n"
        "• **G2** (60–89): Енгил пасайган\n"
        "• **G3a** (45–59): Енгил-ўртача пасайган\n"
        "• **G3b** (30–44): Ўртача-оғир пасайган\n"
        "• **G4** (15–29): Оғир даражада пасайган\n"
        "• **G5** (< 15): Буйрак етишмовчилиги\n\n"
        "**Альбуминурия тоифалари (мг/г ёки мг/ммоль):**\n"
        "• **A1** (< 30 мг/г / < 3 мг/ммоль): Нормал\n"
        "• **A2** (30–300 мг/г / 3–30 мг/ммоль): Микроальбуминурия\n"
        "• **A3** (> 300 мг/г / > 30 мг/ммоль): Макроальбуминурия\n\n"
        "**Хавф гуруҳлари:**\n"
        "🟩 **Паст хавф**: G1A1, G2A1\n"
        "🟨 **Ўртача хавф**: G1A2, G2A2, G3aA1\n"
        "🟧 **Юқори хавф**: G1A3, G2A3, G3aA2, G3bA1\n"
        "🟥 **Жуда юқори хавф**: G3aA3, G3bA2, G3bA3, G4(A1-A3), G5(A1-A3)"
    )
    await message.answer(table_text, reply_markup=get_main_menu_keyboard(is_admin=is_admin), parse_mode="Markdown")


@common_router.message(Command("cancel"))
@common_router.message(F.text == "❌ Бекор қилиш / Бош меню")
async def cmd_cancel(message: Message, state: FSMContext):
    """Ҳолатни бекор қилиб асосий менюга қайтиш."""
    await state.clear()
    is_admin = check_is_admin(message.from_user.id if message.from_user else 0)
    await message.answer(
        "❌ Амал бекор қилинди. Асосий менюга қайтдингиз.",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin)
    )


@common_router.callback_query(F.data == "cancel_calc")
async def cb_cancel(callback: CallbackQuery, state: FSMContext):
    """Inline бекор қилиш тугмаси."""
    await state.clear()
    is_admin = check_is_admin(callback.from_user.id)
    await callback.message.delete()
    await callback.message.answer(
        "❌ Ҳисоблаш бекор қилинди.",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin)
    )
    await callback.answer()


@common_router.callback_query(F.data == "goto_main_menu")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext):
    """Inline асосий менюга қайтиш."""
    await state.clear()
    is_admin = check_is_admin(callback.from_user.id)
    await callback.message.answer(
        "🏠 Асосий меню:",
        reply_markup=get_main_menu_keyboard(is_admin=is_admin)
    )
    await callback.answer()
