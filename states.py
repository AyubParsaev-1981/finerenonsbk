"""
Telegram Bot FSM (Finite State Machine) ҳолатлари.
"""

from aiogram.fsm.state import State, StatesGroup


class FullCalcStates(StatesGroup):
    """Тўлиқ СБК (КФТ + АКН + KDIGO) ҳисоблаш ҳолатлари."""
    gender = State()
    age = State()
    weight = State()
    blood_creatinine_unit = State()
    blood_creatinine = State()
    urine_albumin_unit = State()
    urine_albumin = State()
    urine_creatinine_unit = State()
    urine_creatinine = State()


class GFRCalcStates(StatesGroup):
    """Фақат КФТ (Cockcroft-Gault ва CKD-EPI) ҳисоблаш ҳолатлари."""
    gender = State()
    age = State()
    weight = State()
    blood_creatinine_unit = State()
    blood_creatinine = State()


class ACRCalcStates(StatesGroup):
    """Фақат Сийдик Альбумин/Креатинин нисбати (АКН) ҳисоблаш ҳолатлари."""
    urine_albumin_unit = State()
    urine_albumin = State()
    urine_creatinine_unit = State()
    urine_creatinine = State()


class AdminBroadcastStates(StatesGroup):
    """Админ оммавий хабар тарқатиш ҳолати."""
    waiting_for_message = State()
