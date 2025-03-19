from fastapi import APIRouter

from .views import mas_router

router = APIRouter()
router.include_router(mas_router, prefix="/mas", tags=["common"])
