"""
Админ панель, тўлиқ статистика, CSV экспорт ва хабар тарқатиш модули.
"""

import asyncio
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import BufferedInputFile, CallbackQuery, Message

from config import settings
from database import db
from keyboards import get_admin_inline_keyboard, get_cancel_keyboard, get_main_menu_keyboard
from states import AdminBroadcastStates

admin_router = Router()


def is_admin(user_id: int) -> bool:
    """Фойдаланувчи админ эканлигини текшириш (агар admin_ids бўш бўлса, ҳаммага рухсат)."""
    if not settings.admin_ids:
        return True  # Созланмаган бўлса очиқ
    return user_id in settings.admin_ids


async def format_statistics_text() -> str:
    """Тўлиқ статистика ҳисоботи матнини шакллантириш."""
    stats = await db.get_detailed_statistics()

    stages_text = ""
    if stats["top_stages"]:
        stages_text = "\n".join([f"  • **{st}**: {cnt} та" for st, cnt in stats["top_stages"]])
    else:
        stages_text = "  • _Ҳали маълумот йўқ_"

    risks_text = ""
    if stats["top_risks"]:
        risks_text = "\n".join([f"  • **{rk}**: {cnt} та" for rk, cnt in stats["top_risks"]])
    else:
        risks_text = "  • _Ҳали маълумот йўқ_"

    text = (
        "👑 **БОТНИНГ ТЎЛИҚ СТАТИСТИКАСИ ВА АНАЛИТИКАСИ**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "👥 **Фойдаланувчилар динамикаси:**\n"
        f"• Жами фойдаланувчилар: **{stats['total_users']} нафар**\n"
        f"• Бугун қўшилганлар: **+{stats['new_today']} нафар**\n"
        f"• Охирги 7 кунда: **+{stats['new_7d']} нафар**\n"
        f"• Охирги 30 кунда: **+{stats['new_30d']} нафар**\n\n"
        f"🔥 **Фаоллик:**\n"
        f"• Бугун фаол бўлганлар: **{stats['active_today']} нафар**\n"
        f"• Охирги 7 кунда фаол: **{stats['active_7d']} нафар**\n\n"
        "📈 **Ҳисоб-китоблар кўрсаткичлари:**\n"
        f"• Жами амаллар: **{stats['total_calcs']} та**\n"
        f"  ├ 🩺 Тўлиқ текширувлар (КФТ + АКН): **{stats['full_calcs']} та**\n"
        f"  ├ ⚡ Фақат КФТ (GFR) ҳисоблари: **{stats['gfr_calcs']} та**\n"
        f"  └ 🧪 Фақат АКН (ACR) ҳисоблари: **{stats['acr_calcs']} та**\n\n"
        "🧬 **Энг кўп аниқланган СБК босқичлари:**\n"
        f"{stages_text}\n\n"
        "🚦 **Хавф гуруҳлари тақсимоти:**\n"
        f"{risks_text}\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    return text


@admin_router.message(Command("admin"))
@admin_router.message(Command("stat"))
@admin_router.message(Command("stats"))
@admin_router.message(F.text == "👑 Админ статистика ва бошқарув")
async def show_admin_panel(message: Message, state: FSMContext):
    """Админ панели ва статистикани кўрсатиш."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Кечирасиз, ушбу бўлим фақат администраторлар учун.")
        return

    await state.clear()
    text = await format_statistics_text()
    await message.answer(text, reply_markup=get_admin_inline_keyboard(), parse_mode="Markdown")


@admin_router.callback_query(F.data == "admin_refresh_stat")
async def cb_refresh_stat(callback: CallbackQuery):
    """Статистикани янгилаш."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рухсат йўқ!", show_alert=True)
        return

    text = await format_statistics_text()
    try:
        await callback.message.edit_text(text, reply_markup=get_admin_inline_keyboard(), parse_mode="Markdown")
        await callback.answer("✅ Статистика янгиланди!")
    except Exception:
        await callback.answer("Статистика аллақачон энг сўнгги ҳолатда.")


@admin_router.callback_query(F.data == "admin_export_csv")
async def cb_export_csv(callback: CallbackQuery):
    """Фойдаланувчилар базасини CSV файлда юклаб бериш."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рухсат йўқ!", show_alert=True)
        return

    await callback.answer("⏳ CSV файл тайёрланмоқда...")
    csv_bytes = await db.export_users_csv()
    doc = BufferedInputFile(csv_bytes.read(), filename="users_statistics.csv")
    
    await callback.message.answer_document(
        document=doc,
        caption="📥 **Фойдаланувчиларнинг тўлиқ статистика файли (CSV/Excel)**"
    )


@admin_router.callback_query(F.data == "admin_broadcast")
async def cb_start_broadcast(callback: CallbackQuery, state: FSMContext):
    """Барча фойдаланувчиларга хабар юбориш жараёнини бошлаш."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Рухсат йўқ!", show_alert=True)
        return

    await state.set_state(AdminBroadcastStates.waiting_for_message)
    await callback.message.answer(
        "📢 **Барча фойдаланувчиларга юбормоқчи бўлган хабарингизни ёзинг:**\n\n"
        "_(Матн, расм ёки маълумот киритинг. Бекор қилиш учун /cancel ни босинг)_",
        reply_markup=get_cancel_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@admin_router.message(AdminBroadcastStates.waiting_for_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """Оммавий хабарни тарқатиш."""
    if not is_admin(message.from_user.id):
        return

    user_ids = await db.get_all_user_ids()
    total_users = len(user_ids)

    if total_users == 0:
        await message.answer("⚠️ Базада хабар юбориш учун фойдаланувчилар мавжуд эмас.", reply_markup=get_main_menu_keyboard(is_admin=True))
        await state.clear()
        return

    status_msg = await message.answer(f"⏳ Хабар юбориш бошланмоқда... (Жами: {total_users} та)")
    await state.clear()

    success_count = 0
    failed_count = 0

    for uid in user_ids:
        try:
            await message.copy_to(chat_id=uid)
            success_count += 1
            await asyncio.sleep(0.05)  # Telegram rate limit ҳимояси
        except Exception:
            failed_count += 1

    await status_msg.edit_text(
        f"✅ **Оммавий хабар тарқатиш якунланди!**\n\n"
        f"• Юборилди: **{success_count} та**\n"
        f"• Етиб бормади (блок): **{failed_count} та**\n"
        f"• Жами: **{total_users} та**",
        parse_mode="Markdown"
    )
