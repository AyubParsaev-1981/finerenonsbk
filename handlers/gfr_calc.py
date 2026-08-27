"""
Фақат КФТ (Cockcroft-Gault ва CKD-EPI) ҳисоблаш хэндлерлари.
"""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from calculators import (
    calculate_ckd_epi_2021,
    calculate_cockcroft_gault,
    get_gfr_stage,
)
from database import db
from keyboards import (
    get_blood_creatinine_unit_keyboard,
    get_cancel_keyboard,
    get_gender_inline_keyboard,
    get_main_menu_keyboard,
    get_recalc_inline_keyboard,
)
from states import GFRCalcStates

gfr_calc_router = Router()


@gfr_calc_router.message(F.text == "⚡ КФТ ҳисоблаш (Креатинин, ёш, вазн)")
@gfr_calc_router.callback_query(F.data == "restart_gfr")
async def start_gfr_calc(event: Message | CallbackQuery, state: FSMContext):
    """КФТ ҳисоблашни бошлаш."""
    await state.clear()
    await state.set_state(GFRCalcStates.gender)

    text = (
        "⚡ **Коптокчалар фильтрацияси тезлигини (КФТ) ҳисоблаш**\n\n"
        "1️⃣ Беморнинг **жинсини** танланг:"
    )

    if isinstance(event, CallbackQuery):
        await event.message.answer(text, reply_markup=get_gender_inline_keyboard(prefix="gfr"), parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(
            "Ҳисоблаш бошланди. Хоҳлаган вақтда бекор қилиш учун қуйидаги тугмани босишингиз мумкин.",
            reply_markup=get_cancel_keyboard()
        )
        await event.answer(text, reply_markup=get_gender_inline_keyboard(prefix="gfr"), parse_mode="Markdown")


@gfr_calc_router.callback_query(GFRCalcStates.gender, F.data.startswith("gfr_gender:"))
async def process_gfr_gender(callback: CallbackQuery, state: FSMContext):
    """Жинсни сақлаш ва ёшни сўраш."""
    gender = callback.data.split(":")[1]
    is_female = (gender == "female")
    await state.update_data(is_female=is_female)
    await state.set_state(GFRCalcStates.age)

    gender_str = "👩 Аёл" if is_female else "👨 Эркак"
    await callback.message.edit_text(
        f"✅ Танланди: **{gender_str}**\n\n"
        f"2️⃣ Беморнинг **ёшини** киритинг (масалан: 45):",
        parse_mode="Markdown"
    )
    await callback.answer()


@gfr_calc_router.message(GFRCalcStates.age)
async def process_gfr_age(message: Message, state: FSMContext):
    """Ёшни текшириш ва вазнни сўраш."""
    text = message.text.strip().replace(",", ".")
    try:
        age = int(text)
        if age < 18 or age > 120:
            await message.answer("⚠️ Илтимос, ҳақиқий ёшни киритинг (18 дан 120 гача бўлган бутун сон):")
            return
    except ValueError:
        await message.answer("⚠️ Илтимос, ёшни бутун сон кўринишида киритинг (масалан: 55):")
        return

    await state.update_data(age=age)
    await state.set_state(GFRCalcStates.weight)
    await message.answer("3️⃣ Беморнинг **вазнини (кг)** киритинг (масалан: 72.5):", parse_mode="Markdown")


@gfr_calc_router.message(GFRCalcStates.weight)
async def process_gfr_weight(message: Message, state: FSMContext):
    """Вазнни текшириш ва креатинин бирлигини танлашни таклиф қилиш."""
    text = message.text.strip().replace(",", ".")
    try:
        weight = float(text)
        if weight < 25.0 or weight > 300.0:
            await message.answer("⚠️ Илтимос, ҳақиқий вазнни киритинг (25 дан 300 кг гача):")
            return
    except ValueError:
        await message.answer("⚠️ Илтимос, вазнни рақам кўринишида киритинг (масалан: 68 ёки 75.5):")
        return

    await state.update_data(weight=weight)
    await state.set_state(GFRCalcStates.blood_creatinine_unit)
    await message.answer(
        "4️⃣ Қондаги **креатинин ўлчов бирлигини** танланг:",
        reply_markup=get_blood_creatinine_unit_keyboard(prefix="gfr"),
        parse_mode="Markdown"
    )


@gfr_calc_router.callback_query(GFRCalcStates.blood_creatinine_unit, F.data.startswith("gfr_bcr_unit:"))
async def process_gfr_bcr_unit(callback: CallbackQuery, state: FSMContext):
    """Креатинин бирлигини сақлаш ва қийматини сўраш."""
    unit = callback.data.split(":")[1]
    await state.update_data(creatinine_unit=unit)
    await state.set_state(GFRCalcStates.blood_creatinine)

    unit_name = "мкмоль/л (µmol/L)" if unit == "umol_l" else "мг/дл (mg/dL)"
    example_val = "105" if unit == "umol_l" else "1.2"

    await callback.message.edit_text(
        f"✅ Бирлик: **{unit_name}**\n\n"
        f"5️⃣ Қондаги **креатинин миқдорини** киритинг (масалан: {example_val}):",
        parse_mode="Markdown"
    )
    await callback.answer()


@gfr_calc_router.message(GFRCalcStates.blood_creatinine)
async def process_gfr_bcr_value(message: Message, state: FSMContext):
    """Креатининни текшириш ва КФТ натижасини ҳисоблаб чиқариш."""
    text = message.text.strip().replace(",", ".")
    try:
        creatinine = float(text)
        if creatinine <= 0 or creatinine > 2500:
            await message.answer("⚠️ Илтимос, тўғри креатинин миқдорини киритинг:")
            return
    except ValueError:
        await message.answer("⚠️ Илтимос, креатинин миқдорини рақам сифатида киритинг:")
        return

    data = await state.get_data()
    age = data["age"]
    weight = data["weight"]
    is_female = data["is_female"]
    unit = data["creatinine_unit"]

    # Ҳисоблаш
    cg_crcl = calculate_cockcroft_gault(age, weight, creatinine, unit, is_female)
    ckd_epi = calculate_ckd_epi_2021(age, creatinine, unit, is_female)
    gfr_stage, gfr_desc = get_gfr_stage(ckd_epi)

    # Маълумотлар базасига қайд қилиш
    if message.from_user:
        await db.log_calculation(
            user_id=message.from_user.id,
            calc_type="gfr",
            gfr_val=ckd_epi,
            stage=gfr_stage,
            risk=None
        )

    gender_str = "Аёл" if is_female else "Эркак"
    unit_str = "мкмоль/л" if unit == "umol_l" else "мг/дл"

    result_text = (
        "📋 **КОПТОКЧАЛАР ФИЛЬТРАЦИЯСИ ТЕЗЛИГИ (КФТ) НАТИЖАСИ**\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 **Бемор маълумотлари:**\n"
        f"• Жинси: {gender_str}\n"
        f"• Ёши: {age} ёш\n"
        f"• Вазни: {weight} кг\n"
        f"• Қон креатинини: {creatinine} {unit_str}\n\n"
        "📊 **Ҳисобланган кўрсаткичлар:**\n"
        f"🔹 **Кокрофт-Голт (Cockcroft-Gault)** клиренси: **{cg_crcl} мл/мин**\n"
        f"🔹 **CKD-EPI (2021)** eGFR: **{ckd_epi} мл/мин/1.73м²**\n\n"
        f"🏷 **KDIGO GFR босқичи:** **{gfr_stage}**\n"
        f"📌 **Изоҳ:** {gfr_desc}\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 _Эслатма: Дори воситалари дозасини тўғрилашда Кокрофт-Голт клиренсидан, "
        "СБК босқичини белгилашда эса CKD-EPI формуласидан фойдаланилади._\n\n"
        "👉 Тўлиқ СБК хавф матрицасини аниқлаш учун **АКН (Альбумин/Креатинин нисбати)** ни ҳам текширинг."
    )

    await state.clear()
    await message.answer(
        result_text,
        reply_markup=get_recalc_inline_keyboard("gfr"),
        parse_mode="Markdown"
    )
