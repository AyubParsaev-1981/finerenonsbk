from aiogram import Router
from .common import common_router
from .full_calc import full_calc_router
from .gfr_calc import gfr_calc_router
from .acr_calc import acr_calc_router

main_router = Router()
main_router.include_router(common_router)
main_router.include_router(full_calc_router)
main_router.include_router(gfr_calc_router)
main_router.include_router(acr_calc_router)
