"""
Тўлиқ комплекс текширув (КФТ + АКН + KDIGO СБК босқичи ва хавф матрицаси).
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from calculators import calculate_acr, evaluate_ckd_kdigo
from database import db
from keyboards import (
    get_blood_creatinine_unit_keyboard,
    get_cancel_keyboard,
    get_gender_inline_keyboard,
    get_main_menu_keyboard,
    get_recalc_inline_keyboard,
    get_urine_albumin_unit_keyboard,
    get_urine_creatinine_unit_keyboard,
)
from states import FullCalcStates

full_calc_router = Router()


@full_calc_router.message(F.text == "🩺 Тўлиқ текширув (СБК даражаси + КФТ + АКН)")
@full_calc_router.callback_query(F.data == "restart_full")
async def start_full_calc(event: Message | CallbackQuery, state: FSMContext):
    """Тўлиқ текширувни бошлаш."""
    await state.clear()
    await state.set_state(FullCalcStates.gender)

    text = (
        "🩺 **Сурункали буйрак касаллиги (СБК) тўлиқ текшируви**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "Ушбу текширувда беморнинг КФТ (GFR), сийдикдаги АКН (ACR) ва "
        "халқаро KDIGO таснифи бўйича касаллик босқичи ҳамда хавф гуруҳи аниқланади.\n\n"
        "1️⃣ Беморнинг **жинсини** танланг:"
    )

    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=get_gender_inline_keyboard(prefix="full"), parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(
            "Ҳисоблаш бошланди. Хоҳлаган вақтда бекор қилиш учун қуйидаги тугмани босишингиз мумкин.",
            reply_markup=get_cancel_keyboard()
        )
        await event.answer(text, reply_markup=get_gender_inline_keyboard(prefix="full"), parse_mode="Markdown")


@full_calc_router.callback_query(FullCalcStates.gender, F.data.startswith("full_gender:"))
async def process_full_gender(callback: CallbackQuery, state: FSMContext):
    """Жинсни сақлаш ва ёшни сўраш."""
    gender = callback.data.split(":")[1]
    is_female = (gender == "female")
    await state.update_data(is_female=is_female)
    await state.set_state(FullCalcStates.age)

    gender_str = "👩 Аёл" if is_female else "👨 Эркак"
    await callback.message.edit_text(
        f"✅ Танланди: **{gender_str}**\n\n"
        f"2️⃣ Беморнинг **ёшини** киритинг (масалан: 58):",
        parse_mode="Markdown"
    )
    await callback.answer()


@full_calc_router.message(FullCalcStates.age)
async def process_full_age(message: Message, state: FSMContext):
    """Ёшни текшириш ва вазнни сўраш."""
    text = message.text.strip().replace(",", ".")
    try:
        age = int(text)
        if age < 18 or age > 120:
            await message.answer("⚠️ Илтимос, ҳақиқий ёшни киритинг (18 дан 120 гача бўлган бутун сон):")
            return
    except ValueError:
        await message.answer("⚠️ Илтимос, ёшни бутун сон кўринишида киритинг (масалан: 50):")
        return

    await state.update_data(age=age)
    await state.set_state(FullCalcStates.weight)
    await message.answer("3️⃣ Беморнинг **вазнини (кг)** киритинг (масалан: 74.0):", parse_mode="Markdown")


@full_calc_router.message(FullCalcStates.weight)
async def process_full_weight(message: Message, state: FSMContext):
    """Вазнни текшириш ва қон креатинини бирлигини сўраш."""
    text = message.text.strip().replace(",", ".")
    try:
        weight = float(text)
        if weight < 25.0 or weight > 300.0:
            await message.answer("⚠️ Илтимос, ҳақиқий вазнни киритинг (25 дан 300 кг гача):")
            return
    except ValueError:
        await message.answer("⚠️ Илтимос, вазнни рақам кўринишида киритинг (масалан: 70 ёки 68.5):")
        return

    await state.update_data(weight=weight)
    await state.set_state(FullCalcStates.blood_creatinine_unit)
    await message.answer(
        "4️⃣ Қондаги **креатинин ўлчов бирлигини** танланг:",
        reply_markup=get_blood_creatinine_unit_keyboard(prefix="full"),
        parse_mode="Markdown"
    )


@full_calc_router.callback_query(FullCalcStates.blood_creatinine_unit, F.data.startswith("full_bcr_unit:"))
async def process_full_bcr_unit(callback: CallbackQuery, state: FSMContext):
    """Қон креатинини бирлигини сақлаш ва қийматини сўраш."""
    unit = callback.data.split(":")[1]
    await state.update_data(blood_creatinine_unit=unit)
    await state.set_state(FullCalcStates.blood_creatinine)

    unit_name = "мкмоль/л (µmol/L)" if unit == "umol_l" else "мг/дл (mg/dL)"
    example_val = "115" if unit == "umol_l" else "1.3"

    await callback.message.edit_text(
        f"✅ Бирлик: **{unit_name}**\n\n"
        f"5️⃣ Қондаги **креатинин миқдорини** киритинг (масалан: {example_val}):",
        parse_mode="Markdown"
    )
    await callback.answer()


@full_calc_router.message(FullCalcStates.blood_creatinine)
async def process_full_bcr_value(message: Message, state: FSMContext):
    """Қон креатинини текшириш ва сийдик альбумини бирлигини сўраш."""
    text = message.text.strip().replace(",", ".")
    try:
        bcr = float(text)
        if bcr <= 0 or bcr > 2500:
            await message.answer("⚠️ Илтимос, тўғри креатинин миқдорини киритинг:")
            return
    except ValueError:
        await message.answer("⚠️ Илтимос, креатинин миқдорини рақам сифатида киритинг:")
        return

    await state.update_data(blood_creatinine=bcr)
    await state.set_state(FullCalcStates.urine_albumin_unit)

    await message.answer(
        "6️⃣ Сийдикдаги **альбумин ўлчов бирлигини** танланг:",
        reply_markup=get_urine_albumin_unit_keyboard(prefix="full"),
        parse_mode="Markdown"
    )


@full_calc_router.callback_query(FullCalcStates.urine_albumin_unit, F.data.startswith("full_ualb_unit:"))
async def process_full_alb_unit(callback: CallbackQuery, state: FSMContext):
    """Сийдик альбумини бирлигини сақлаш ва қийматини сўраш."""
    unit = callback.data.split(":")[1]
    await state.update_data(urine_albumin_unit=unit)
    await state.set_state(FullCalcStates.urine_albumin)

    unit_name = "мг/л (mg/L)" if unit == "mg_l" else "мг/дл (mg/dL)"
    example_val = "60" if unit == "mg_l" else "6.0"

    await callback.message.edit_text(
        f"✅ Бирлик: **{unit_name}**\n\n"
        f"7️⃣ Сийдикдаги **альбумин миқдорини** киритинг (масалан: {example_val}):",
        parse_mode="Markdown"
    )
    await callback.answer()


@full_calc_router.message(FullCalcStates.urine_albumin)
async def process_full_alb_value(message: Message, state: FSMContext):
    """Сийдик альбуминини текшириш ва сийдик креатинини бирлигини сўраш."""
    text = message.text.strip().replace(",", ".")
    try:
        alb = float(text)
        if alb < 0 or alb > 50000:
            await message.answer("⚠️ Илтимос, тўғри альбумин миқдорини киритинг:")
            return
    except ValueError:
        await message.answer("⚠️ Илтимос, альбумин миқдорини рақам сифатида киритинг:")
        return

    await state.update_data(urine_albumin=alb)
    await state.set_state(FullCalcStates.urine_creatinine_unit)

    await message.answer(
        "8️⃣ Сийдикдаги **креатинин ўлчов бирлигини** танланг:",
        reply_markup=get_urine_creatinine_unit_keyboard(prefix="full"),
        parse_mode="Markdown"
    )


@full_calc_router.callback_query(FullCalcStates.urine_creatinine_unit, F.data.startswith("full_ucr_unit:"))
async def process_full_cr_unit(callback: CallbackQuery, state: FSMContext):
    """Сийдик креатинини бирлигини сақлаш ва қийматини сўраш."""
    unit = callback.data.split(":")[1]
    await state.update_data(urine_creatinine_unit=unit)
    await state.set_state(FullCalcStates.urine_creatinine)

    if unit == "g_l":
        unit_name = "г/л (g/L)"
        example_val = "1.0"
    elif unit == "mmol_l":
        unit_name = "ммоль/л (mmol/L)"
        example_val = "8.8"
    else:
        unit_name = "мг/дл (mg/dL)"
        example_val = "100"

    await callback.message.edit_text(
        f"✅ Бирлик: **{unit_name}**\n\n"
        f"9️⃣ Сийдикдаги **креатинин миқдорини** киритинг (масалан: {example_val}):",
        parse_mode="Markdown"
    )
    await callback.answer()


@full_calc_router.message(FullCalcStates.urine_creatinine)
async def process_full_cr_value(message: Message, state: FSMContext):
    """Якуний ҳисоб-китоб ва комплекс KDIGO натижасини шакллантириш."""
    text = message.text.strip().replace(",", ".")
    try:
        ucr = float(text)
        if ucr <= 0 or ucr > 10000:
            await message.answer("⚠️ Илтимос, тўғри креатинин миқдорини (0 дан катта) киритинг:")
            return
    except ValueError:
        await message.answer("⚠️ Илтимос, креатинин миқдорини рақам сифатида киритинг:")
        return

    data = await state.get_data()
    age = data["age"]
    weight = data["weight"]
    is_female = data["is_female"]
    bcr = data["blood_creatinine"]
    bcr_unit = data["blood_creatinine_unit"]
    ualb = data["urine_albumin"]
    ualb_unit = data["urine_albumin_unit"]
    ucr_unit = data["urine_creatinine_unit"]

    # АКН ҳисоблаш
    acr_res = calculate_acr(ualb, ualb_unit, ucr, ucr_unit)

    # Тўлиқ KDIGO баҳоси
    ckd_res = evaluate_ckd_kdigo(
        age=age,
        weight_kg=weight,
        creatinine=bcr,
        creatinine_unit=bcr_unit,
        is_female=is_female,
        acr_result=acr_res
    )

    # Маълумотлар базасига қайд қилиш
    if message.from_user:
        await db.log_calculation(
            user_id=message.from_user.id,
            calc_type="full",
            gfr_val=ckd_res.gfr.ckd_epi,
            acr_val=acr_res.acr_mg_g,
            stage=ckd_res.combined_stage,
            risk=ckd_res.risk_level
        )

    gender_str = "Аёл" if is_female else "Эркак"
    bcr_unit_str = "мкмоль/л" if bcr_unit == "umol_l" else "мг/дл"

    result_text = (
        "🏥 **СУРУНКАЛИ БУЙРАК КАСАЛЛИГИ (СБК / ХБП) ТЎЛИҚ ҲИСОБОТИ**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Бемор кўрсаткичлари:**\n"
        f"• Жинси: {gender_str} | Ёши: {age} ёш | Вазни: {weight} кг\n"
        f"• Қон креатинини: {bcr} {bcr_unit_str}\n\n"
        "🔹 **1. Коптокчалар фильтрацияси тезлиги (КФТ):**\n"
        f"• Кокрофт-Голт клиренси: **{ckd_res.gfr.cockcroft_gault} мл/мин**\n"
        f"• CKD-EPI (2021) eGFR: **{ckd_res.gfr.ckd_epi} мл/мин/1.73м²**\n"
        f"• GFR босқичи: **{ckd_res.gfr.gfr_stage}** ({ckd_res.gfr.gfr_description})\n\n"
        "🔹 **2. Альбумин/Креатинин нисбати (АКН):**\n"
        f"• АКН: **{acr_res.acr_mg_g} мг/г** ({acr_res.acr_mg_mmol} мг/ммоль)\n"
        f"• Альбуминурия тоифаси: **{acr_res.albuminuria_stage}** ({acr_res.albuminuria_description})\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷 **KDIGO Бўйича СБК Босқичи:** **{ckd_res.combined_stage}**\n"
        f"{ckd_res.risk_emoji} **Асоратлар хавф даражаси:** **{ckd_res.risk_level}**\n"
        f"📅 **Назорат частотаси:** {ckd_res.monitoring_frequency}\n\n"
        f"📋 **Клиник тавсиялар:**\n"
        f"{ckd_res.recommendations}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚠️ _Эслатма: Натижалар фақат кўмакчи маълумот ҳисобланади. Аниқ ташхис ва даволаш учун шифокор кўриги шарт!_"
    )

    await state.clear()
    await message.answer(
        result_text,
        reply_markup=get_recalc_inline_keyboard("full"),
        parse_mode="Markdown"
    )
