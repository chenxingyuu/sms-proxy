import hashlib
import json
from dataclasses import dataclass
from typing import Union, List, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Depends
from pydantic import BaseModel

from cores.config import settings
from cores.log import LOG
from cores.redis import ASYNC_REDIS

mas_router = APIRouter()


# 鉴权依赖项
def verify_api_key(x_api_key: Optional[str] = Header(None)):
    if x_api_key != settings.security.api_key:
        LOG.warning("API Key 校验失败")
        raise HTTPException(status_code=401, detail="Unauthorized")


# 请求体定义
class SmsRequest(BaseModel):
    phone_numbers: Union[List[str], str]
    message: Union[Dict, str]


@dataclass
class Message:
    phone_number: str
    message: str


async def enqueue_sms(messages: List[Message]):
    for message in messages:
        msg_hash = hashlib.md5(f"{message.phone_number}_{message.message}".encode()).hexdigest()
        cache_key = f"mas:sms:{msg_hash}"

        if not await ASYNC_REDIS.set(cache_key, "sent", ex=60, nx=True):
            LOG.warning(f"相同短信 60 秒内不重复发送 {message = }")
            continue

        # 存入 Redis List
        sms_data = {
            "phone_number": message.phone_number,
            "message": message.message
        }
        await ASYNC_REDIS.lpush("sms_queue", json.dumps(sms_data))


# 短信发送接口
@mas_router.post("/send_sms", dependencies=[Depends(verify_api_key)])
async def send_sms(request: SmsRequest):
    LOG.info(f"请求参数: {request = }")

    if not request.phone_numbers or not request.message:
        raise HTTPException(status_code=400, detail="手机号或内容不能为空")

    if isinstance(request.message, dict):
        request.phone_numbers = list(request.message.keys())
    if isinstance(request.phone_numbers, str):
        request.phone_numbers = request.phone_numbers.split(",")
    if isinstance(request.message, str):
        request.message = {phone_number: request.message for phone_number in request.phone_numbers}

    messages = [
        Message(
            phone_number=phone_number.strip(),
            message=request.message[phone_number]
        )
        for phone_number in request.phone_numbers
    ]
    LOG.info(f"短信发送列表: {messages}")

    await enqueue_sms(messages)

    return {"message": "SMS sent successfully"}
