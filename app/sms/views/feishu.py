import requests
from fastapi import APIRouter
from starlette.requests import Request

from cores.log import LOG

feishu_router = APIRouter()


@feishu_router.post("/send/{token}")
async def send(token: str, request: Request):
    LOG.info(f"请求参数: {token} {request = }")
    json_data = await request.json()

    response = requests.post(
        url=f"https://open.feishu.cn/open-apis/bot/v2/hook/{token}",
        json=json_data,
    )

    LOG.info(response.json())
    return response.json()
