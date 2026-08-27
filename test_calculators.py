"""
Ҳисоблаш модулини текшириш учун тест скрипти.
"""

import sys

# Windows консолида UTF-8 белгиларини тўғри кўрсатиш учун
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

from calculators import (
    calculate_cockcroft_gault,
    calculate_ckd_epi_2021,
    calculate_acr,
    evaluate_ckd_kdigo,
    convert_creatinine_to_mg_dl
)


def run_tests():
    print("=== ТЕСТ 1: Креатинин конвертацияси ===")
    assert round(convert_creatinine_to_mg_dl(88.4, "umol_l"), 2) == 1.0
    assert convert_creatinine_to_mg_dl(1.2, "mg_dl") == 1.2
    print("[OK] Креатинин конвертацияси муваффақиятли!")

    print("\n=== ТЕСТ 2: Кокрофт-Голт ва CKD-EPI (Эркак, 60 ёш, 75 кг, Scr = 1.0 мг/дл) ===")
    cg_male = calculate_cockcroft_gault(60, 75.0, 1.0, "mg_dl", is_female=False)
    assert cg_male == 83.3, f"Expected 83.3, got {cg_male}"
    
    ckd_male = calculate_ckd_epi_2021(60, 1.0, "mg_dl", is_female=False)
    print(f"Cockcroft-Gault: {cg_male} мл/мин, CKD-EPI: {ckd_male} мл/мин/1.73м²")
    assert 70.0 <= ckd_male <= 90.0
    print("[OK] КФТ ҳисоблаш муваффақиятли!")

    print("\n=== ТЕСТ 3: АКН (ACR) ҳисоблаш ===")
    acr_res = calculate_acr(150.0, "mg_l", 1.0, "g_l")
    assert acr_res.acr_mg_g == 150.0
    assert acr_res.albuminuria_stage == "A2"
    print(f"АКН: {acr_res.acr_mg_g} мг/г ({acr_res.albuminuria_stage}) - {acr_res.albuminuria_description}")
    print("[OK] АКН ҳисоблаш муваффақиятли!")

    print("\n=== ТЕСТ 4: KDIGO Тўлиқ СБК баҳоси ===")
    eval_res = evaluate_ckd_kdigo(
        age=70,
        weight_kg=65.0,
        creatinine=130.0,
        creatinine_unit="umol_l",
        is_female=True,
        acr_result=acr_res
    )
    print(f"Босқич: {eval_res.combined_stage}, Хавф: {eval_res.risk_emoji} {eval_res.risk_level}")
    print(f"КФТ (Кокрофт): {eval_res.gfr.cockcroft_gault} мл/мин")
    print(f"eGFR (CKD-EPI): {eval_res.gfr.ckd_epi} мл/мин/1.73м² ({eval_res.gfr.gfr_stage})")
    assert eval_res.risk_level in ["Юқори хавф (High Risk)", "Жуда юқори хавф (Very High Risk)", "Ўртача ошган хавф (Moderate Risk)"]
    print("[OK] KDIGO баҳолаш муваффақиятли!")

    print("\n[SUCCESS] БАРЧА ТЕСТЛАР МУВАФФАҚИЯТЛИ ЎТДИ!")


if __name__ == "__main__":
    run_tests()
