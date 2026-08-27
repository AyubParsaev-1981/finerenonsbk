"""
Фақат Сийдикдаги Альбумин/Креатинин нисбати (АКН / ACR) ҳисоблаш хэндлерлари.
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from calculators import calculate_acr
from database import db
from keyboards import (
    get_cancel_keyboard,
    get_recalc_inline_keyboard,
    get_urine_albumin_unit_keyboard,
    get_urine_creatinine_unit_keyboard,
)
from states import ACRCalcStates

acr_calc_router = Router()


@acr_calc_router.message(F.text == "🧪 АКН ҳисоблаш (Альбумин/Креатинин)")
@acr_calc_router.callback_query(F.data == "restart_acr")
async def start_acr_calc(event: Message | CallbackQuery, state: FSMContext):
    """АКН ҳисоблашни бошлаш."""
    await state.clear()
    await state.set_state(ACRCalcStates.urine_albumin_unit)

    text = (
        "🧪 **Сийдикдаги Альбумин/Креатинин нисбатини (АКН / ACR) ҳисоблаш**\n\n"
        "1️⃣ Сийдикдаги **альбумин ўлчов бирлигини** танланг:"
    )

    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=get_urine_albumin_unit_keyboard(prefix="acr"), parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(
            "Ҳисоблаш бошланди. Хоҳлаган вақтда бекор қилиш учун қуйидаги тугмани босишингиз мумкин.",
            reply_markup=get_cancel_keyboard()
        )
        await event.answer(text, reply_markup=get_urine_albumin_unit_keyboard(prefix="acr"), parse_mode="Markdown")


@acr_calc_router.callback_query(ACRCalcStates.urine_albumin_unit, F.data.startswith("acr_ualb_unit:"))
async def process_acr_alb_unit(callback: CallbackQuery, state: FSMContext):
    """Альбумин бирлигини сақлаш ва қийматини сўраш."""
    unit = callback.data.split(":")[1]
    await state.update_data(albumin_unit=unit)
    await state.set_state(ACRCalcStates.urine_albumin)

    unit_name = "мг/л (mg/L)" if unit == "mg_l" else "мг/дл (mg/dL)"
    example_val = "45" if unit == "mg_l" else "4.5"

    await callback.message.edit_text(
        f"✅ Бирлик: **{unit_name}**\n\n"
        f"2️⃣ Сийдикдаги **альбумин миқдорини** киритинг (масалан: {example_val}):",
        parse_mode="Markdown"
    )
    await callback.answer()


@acr_calc_router.message(ACRCalcStates.urine_albumin)
async def process_acr_alb_value(message: Message, state: FSMContext):
    """Альбумин қийматини текшириш ва креатинин бирлигини сўраш."""
    text = message.text.strip().replace(",", ".")
    try:
        alb_val = float(text)
        if alb_val < 0 or alb_val > 50000:
            await message.answer("⚠️ Илтимос, тўғри альбумин миқдорини киритинг:")
            return
    except ValueError:
        await message.answer("⚠️ Илтимос, альбумин миқдорини рақам сифатида киритинг:")
        return

    await state.update_data(urine_albumin=alb_val)
    await state.set_state(ACRCalcStates.urine_creatinine_unit)

    await message.answer(
        "3️⃣ Сийдикдаги **креатинин ўлчов бирлигини** танланг:",
        reply_markup=get_urine_creatinine_unit_keyboard(prefix="acr"),
        parse_mode="Markdown"
    )


@acr_calc_router.callback_query(ACRCalcStates.urine_creatinine_unit, F.data.startswith("acr_ucr_unit:"))
async def process_acr_cr_unit(callback: CallbackQuery, state: FSMContext):
    """Креатинин бирлигини сақлаш ва қийматини сўраш."""
    unit = callback.data.split(":")[1]
    await state.update_data(creatinine_unit=unit)
    await state.set_state(ACRCalcStates.urine_creatinine)

    if unit == "g_l":
        unit_name = "г/л (g/L)"
        example_val = "1.2"
    elif unit == "mmol_l":
        unit_name = "ммоль/л (mmol/L)"
        example_val = "10.5"
    else:
        unit_name = "мг/дл (mg/dL)"
        example_val = "120"

    await callback.message.edit_text(
        f"✅ Бирлик: **{unit_name}**\n\n"
        f"4️⃣ Сийдикдаги **креатинин миқдорини** киритинг (масалан: {example_val}):",
        parse_mode="Markdown"
    )
    await callback.answer()


@acr_calc_router.message(ACRCalcStates.urine_creatinine)
async def process_acr_cr_value(message: Message, state: FSMContext):
    """Креатинин қийматини текшириш ва АКН ҳисобини чиқариш."""
    text = message.text.strip().replace(",", ".")
    try:
        cr_val = float(text)
        if cr_val <= 0 or cr_val > 10000:
            await message.answer("⚠️ Илтимос, тўғри креатинин миқдорини (0 дан катта) киритинг:")
            return
    except ValueError:
        await message.answer("⚠️ Илтимос, креатинин миқдорини рақам сифатида киритинг:")
        return

    data = await state.get_data()
    alb_val = data["urine_albumin"]
    alb_unit = data["albumin_unit"]
    cr_unit = data["creatinine_unit"]

    acr_res = calculate_acr(alb_val, alb_unit, cr_val, cr_unit)

    # Маълумотлар базасига қайд қилиш
    if message.from_user:
        await db.log_calculation(
            user_id=message.from_user.id,
            calc_type="acr",
            acr_val=acr_res.acr_mg_g,
            stage=acr_res.albuminuria_stage,
            risk=None
        )

    # Эможи белгиси
    if acr_res.albuminuria_stage == "A1":
        emoji = "🟢"
    elif acr_res.albuminuria_stage == "A2":
        emoji = "🟡"
    else:
        emoji = "🔴"

    result_text = (
        "📋 **АЛЬБУМИН/КРЕАТИНИН НИСБАТИ (АКН / ACR) НАТИЖАСИ**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 **Ҳисобланган АКН кўрсаткичлари:**\n"
        f"• **{acr_res.acr_mg_g} мг/г** (мг альбумин / г креатинин)\n"
        f"• **{acr_res.acr_mg_mmol} мг/ммоль** (мг альбумин / ммоль креатинин)\n\n"
        f"{emoji} **Альбуминурия тоифаси:** **{acr_res.albuminuria_stage}**\n"
        f"📌 **Изоҳ:** {acr_res.albuminuria_description}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 _АКН (ACR) бир марталик сийдик таҳлилидан олинади ва суткалик оқсил йўқотишни энг юқори аниқликда акс эттиради._"
    )

    await state.clear()
    await message.answer(
        result_text,
        reply_markup=get_recalc_inline_keyboard("acr"),
        parse_mode="Markdown"
    )
