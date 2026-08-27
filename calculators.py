"""
Тиббий ҳисоб-китоблар ва KDIGO таснифи модули.
Ушбу модулда:
1. Кокрофт-Голт (Cockcroft-Gault) формуласи бўйича КФТ / Креатинин клиренси
2. CKD-EPI (2021) формуласи бўйича eGFR
3. Сийдикдаги Альбумин/Креатинин нисбати (АКН / ACR)
4. Халқаро KDIGO (2024/2012) бўйича СБК (ХБП) босқичи ва хавф матрицаси
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class GFRResult:
    cockcroft_gault: float  # мл/мин
    ckd_epi: float          # мл/мин/1.73 м²
    gfr_stage: str          # G1, G2, G3a, G3b, G4, G5
    gfr_description: str    # Босқич изоҳи


@dataclass
class ACRResult:
    acr_mg_g: float         # мг/г
    acr_mg_mmol: float      # мг/ммоль
    albuminuria_stage: str  # A1, A2, A3
    albuminuria_description: str  # Босқич изоҳи


@dataclass
class CKDStageResult:
    gfr: GFRResult
    acr: Optional[ACRResult]
    combined_stage: str     # Масалан: G3aA2
    risk_level: str         # Паст, Ўртача, Юқори, Жуда юқори
    risk_emoji: str         # 🟩, 🟨, 🟧, 🟥
    monitoring_frequency: str  # Назорат частотаси
    recommendations: str    # Клиник тавсиялар


def convert_creatinine_to_mg_dl(value: float, unit: str) -> float:
    """Қондаги креатининни мг/дл га ўтказади."""
    if unit == "umol_l":  # мкмоль/л
        return value / 88.4
    return value  # аллақачон мг/дл


def convert_creatinine_to_umol_l(value: float, unit: str) -> float:
    """Қондаги креатининни мкмоль/л га ўтказади."""
    if unit == "mg_dl":  # мг/дл
        return value * 88.4
    return value  # аллақачон мкмоль/л


def calculate_cockcroft_gault(
    age: int,
    weight_kg: float,
    creatinine: float,
    creatinine_unit: str,
    is_female: bool
) -> float:
    """
    Кокрофт-Голт (Cockcroft-Gault) формуласи:
    CrCl (мл/мин) = [(140 - ёш) * вазн (кг)] / [72 * Scr (мг/дл)] * (0.85 агар аёл бўлса)
    """
    scr_mg_dl = convert_creatinine_to_mg_dl(creatinine, creatinine_unit)
    if scr_mg_dl <= 0:
        return 0.0

    crcl = ((140 - age) * weight_kg) / (72.0 * scr_mg_dl)
    if is_female:
        crcl *= 0.85
    return round(crcl, 1)


def calculate_ckd_epi_2021(
    age: int,
    creatinine: float,
    creatinine_unit: str,
    is_female: bool
) -> float:
    """
    CKD-EPI (2021) формуласи (ирқий коэффицентсиз халқаро янгиланган стандарт):
    eGFR = 142 * min(Scr/kappa, 1)^alpha * max(Scr/kappa, 1)^(-1.200) * 0.9938^age * (1.012 агар аёл бўлса)
    """
    scr_mg_dl = convert_creatinine_to_mg_dl(creatinine, creatinine_unit)
    if scr_mg_dl <= 0:
        return 0.0

    if is_female:
        kappa = 0.7
        alpha = -0.241
        gender_mult = 1.012
    else:
        kappa = 0.9
        alpha = -0.302
        gender_mult = 1.0

    scr_over_kappa = scr_mg_dl / kappa
    min_part = min(scr_over_kappa, 1.0) ** alpha
    max_part = max(scr_over_kappa, 1.0) ** (-1.200)
    age_part = 0.9938 ** age

    egfr = 142.0 * min_part * max_part * age_part * gender_mult
    return round(egfr, 1)


def get_gfr_stage(egfr: float) -> Tuple[str, str]:
    """GFR қиймати бўйича KDIGO босқичини аниқлайди."""
    if egfr >= 90:
        return "G1", "Нормал ёки юқори (Normal/High)"
    elif egfr >= 60:
        return "G2", "Енгил пасайган (Mildly decreased)"
    elif egfr >= 45:
        return "G3a", "Енгил-ўртача пасайган (Mild to moderate)"
    elif egfr >= 30:
        return "G3b", "Ўртача-оғир пасайган (Moderate to severe)"
    elif egfr >= 15:
        return "G4", "Оғир даражада пасайган (Severely decreased)"
    else:
        return "G5", "Буйрак етишмовчилиги / Терминал босқич (Kidney failure)"


def calculate_acr(
    urine_albumin: float,
    albumin_unit: str,
    urine_creatinine: float,
    creatinine_unit: str
) -> ACRResult:
    """
    Сийдикдаги альбумин-креатинин нисбатини (АКН / ACR) ҳисоблайди.
    
    Бирликлар:
    - albumin_unit: 'mg_l' (мг/л) ёки 'mg_dl' (мг/дл)
    - creatinine_unit: 'g_l' (г/л), 'mg_dl' (мг/дл), 'mmol_l' (ммоль/л)
    """
    # Альбуминни мг/л га ўтказиш
    if albumin_unit == "mg_dl":
        alb_mg_l = urine_albumin * 10.0
    else:  # mg_l
        alb_mg_l = urine_albumin

    # Креатининни г/л га ўтказиш
    if creatinine_unit == "mg_dl":
        cr_g_l = urine_albumin_cr_mg_dl = urine_creatinine / 100.0
    elif creatinine_unit == "mmol_l":
        cr_g_l = urine_creatinine / 8.84
    else:  # g_l
        cr_g_l = urine_creatinine

    if cr_g_l <= 0:
        acr_mg_g = 0.0
        acr_mg_mmol = 0.0
    else:
        # АКН (мг/г) = Альбумин (мг/л) / Креатинин (г/л)
        acr_mg_g = alb_mg_l / cr_g_l
        # АКН (мг/ммоль) = АКН (мг/г) / 8.84
        acr_mg_mmol = acr_mg_g / 8.84

    acr_mg_g = round(acr_mg_g, 1)
    acr_mg_mmol = round(acr_mg_mmol, 1)

    if acr_mg_g < 30:
        stage = "A1"
        desc = "Нормал ёки бироз ошган (<30 мг/г ёки <3 мг/ммоль)"
    elif acr_mg_g <= 300:
        stage = "A2"
        desc = "Ўртача ошган / Микроальбуминурия (30-300 мг/г ёки 3-30 мг/ммоль)"
    else:
        stage = "A3"
        desc = "Кескин ошган / Макроальбуминурия (>300 мг/г ёки >30 мг/ммоль)"

    return ACRResult(
        acr_mg_g=acr_mg_g,
        acr_mg_mmol=acr_mg_mmol,
        albuminuria_stage=stage,
        albuminuria_description=desc
    )


def evaluate_ckd_kdigo(
    age: int,
    weight_kg: float,
    creatinine: float,
    creatinine_unit: str,
    is_female: bool,
    acr_result: Optional[ACRResult] = None
) -> CKDStageResult:
    """
    KDIGO (2024/2012) бўйича тўлиқ СБК баҳоси ва хавф матрицаси.
    """
    cg_crcl = calculate_cockcroft_gault(age, weight_kg, creatinine, creatinine_unit, is_female)
    ckd_epi = calculate_ckd_epi_2021(age, creatinine, creatinine_unit, is_female)
    gfr_stage, gfr_desc = get_gfr_stage(ckd_epi)

    gfr_res = GFRResult(
        cockcroft_gault=cg_crcl,
        ckd_epi=ckd_epi,
        gfr_stage=gfr_stage,
        gfr_description=gfr_desc
    )

    if acr_result is None:
        # Фақат GFR асосида дастлабки хулоса
        risk_level = "КФТ бўйича баҳоланди"
        risk_emoji = "ℹ️"
        comb_stage = gfr_stage
        monitoring = "Альбуминурия даражаси аниқланмаган."
        recommendations = "Буйрак шикастланишини аниқлаш учун сийдикдаги альбумин/креатинин нисбатини (АКН) топшириш тавсия этилади."
    else:
        comb_stage = f"{gfr_stage}{acr_result.albuminuria_stage}"
        a_stage = acr_result.albuminuria_stage

        # KDIGO Хавф матрицаси:
        # Green (Паст): G1A1, G2A1
        # Yellow (Ўртача): G1A2, G2A2, G3aA1
        # Orange (Юқори): G1A3, G2A3, G3aA2, G3bA1
        # Red (Жуда юқори): G3aA3, G3bA2, G3bA3, G4(A1,A2,A3), G5(A1,A2,A3)

        if gfr_stage in ["G1", "G2"] and a_stage == "A1":
            risk_level = "Паст хавф (Low Risk)"
            risk_emoji = "🟩"
            monitoring = "Йилига 1 марта скрининг текшируви (агар хавф омиллари мавжуд бўлса)."
            recommendations = (
                "• Буйрак фаолияти сақланган.\n"
                "• Агар буйракнинг бошқа шикастланиш белгилари (УТТ, сийдик чўкмаси) бўлмаса, СБК йўқ деб ҳисобланади.\n"
                "• Соғлом турмуш тарзи, сув баланси ва қон босимини назорат қилиб боринг."
            )
        elif (gfr_stage in ["G1", "G2"] and a_stage == "A2") or (gfr_stage == "G3a" and a_stage == "A1"):
            risk_level = "Ўртача ошган хавф (Moderate Risk)"
            risk_emoji = "🟨"
            monitoring = "Йилига камида 1 марта КФТ ва сийдик АКН текшируви."
            recommendations = (
                "• Сурункали буйрак касаллигининг эрта босқичи белгилари мавжуд.\n"
                "• Қон босимини (<130/80 мм сим.уст) ва қанд миқдорини қатъий назорат қилинг.\n"
                "• Терапевт ёки нефролог кўригидан ўтиш тавсия этилади.\n"
                "• Нефротоксик дорилар (НҚЯҚ / НПВС, баъзи антибиотиклар)ни назоратсиз қабул қилманг."
            )
        elif (gfr_stage in ["G1", "G2"] and a_stage == "A3") or (gfr_stage == "G3a" and a_stage == "A2") or (gfr_stage == "G3b" and a_stage == "A1"):
            risk_level = "Юқори хавф (High Risk)"
            risk_emoji = "🟧"
            monitoring = "Йилига камида 2 марта шифокор кўриги ва таҳлиллар."
            recommendations = (
                "• Касаллик авж олиш хавфи юқори.\n"
                "• Кардиоваскуляр ва буйрак асоратлари хавфи ошган.\n"
                "• Нефролог маслаҳати, нефропротектив даво (иАПФ/БРА, SGLT2 ингибиторлари) тайинланиши зарур.\n"
                "• Ош тузини чеклаш (<5 г/кун) ва оқсил истеъмолини назорат қилиш тавсия этилади."
            )
        else:
            # Red zone
            risk_level = "Жуда юқори хавф (Very High Risk)"
            risk_emoji = "🟥"
            monitoring = "Йилига 3-4 марта ёки доимий нефролог назорати."
            recommendations = (
                "• Буйрак фаолияти жиддий пасайган ёки макроальбуминурия мавжуд.\n"
                "• Шошилинч нефролог назорати ва индивидуал даволаш режаси зарур.\n"
                "• Анемия, минерал-суяк алмашинуви бузилишлари ва гиперкалиемияни даволаш.\n"
                "• G4-G5 босқичларида: Буйрак ўрнини босувчи терапияга (гемодиализ, перитонеал диализ, трансплантация) тайёргарлик."
            )

    return CKDStageResult(
        gfr=gfr_res,
        acr=acr_result,
        combined_stage=comb_stage,
        risk_level=risk_level,
        risk_emoji=risk_emoji,
        monitoring_frequency=monitoring,
        recommendations=recommendations
    )
