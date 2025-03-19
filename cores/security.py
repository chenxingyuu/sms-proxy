# 鉴权依赖项
from typing import Optional

from fastapi import HTTPException, Header

from cores.config import settings
from cores.log import LOG


def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != settings.security.api_key:
        LOG.warning("API Key 校验失败")
        raise HTTPException(status_code=401, detail="Unauthorized")
