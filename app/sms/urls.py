from fastapi import APIRouter

from .views.feishu import feishu_router
from .views.mas import mas_router

router = APIRouter()
router.include_router(mas_router, prefix="/mas", tags=["sms"])
router.include_router(feishu_router, prefix="/feishu", tags=["sms"])
