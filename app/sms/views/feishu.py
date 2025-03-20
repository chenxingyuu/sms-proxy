import hashlib
import json
import re
from typing import List, Optional

import requests
from fastapi import APIRouter
from pydantic import BaseModel
from starlette.requests import Request

from cores.config import settings
from cores.log import LOG
from cores.redis import ASYNC_REDIS

feishu_router = APIRouter()


class FilterRule(BaseModel):
    include: List[str]
    exclude: List[str]
    expires: int = 0  # 过期时间（秒）


def search_value(data: dict, key: str):
    """
    递归获取字典中的值
    :param data:
    :param key:
    :return:
    """
    if isinstance(data, dict):
        for k, v in data.items():
            if k == key and len(v.strip()) > 0:
                yield v
            else:
                yield from search_value(v, key)
    elif isinstance(data, list):
        for item in data:
            yield from search_value(item, key)


def apply_include(contents: list, include: list):
    """
    >>> apply_include(["a", "b", "c"], ["a", "b"])
    True
    >>> apply_include(["a", "b", "c"], ["d", "e"])
    False
    >>> apply_include(["a", "b", "c"], ["a"])
    True
    >>> apply_include(["a", "b", "c"], [])
    True
    >>> apply_include([], ["a", "b", "c"])
    True

    :param contents:
    :param include:
    :return:
    """
    if not include or not contents:
        return True
    for item in contents:
        for pattern in include:
            if re.search(pattern, item):
                return True
    else:
        return False


def apply_exclude(contents: list, exclude: list):
    """
    >>> apply_exclude(["abc", "bc", "c"], ["a", "b"])
    False
    >>> apply_exclude(["abc", "bc", "c"], ["d", "e"])
    True
    >>> apply_exclude(["abc", "bc"], ["c"])
    False
    >>> apply_exclude(["abc", "bc", "c"], [])
    True
    >>> apply_exclude([], ["a", "b", "c"])
    True

    :param contents:
    :param exclude:
    :return:
    """
    for item in contents:
        for pattern in exclude:
            if re.search(pattern, item):
                return False
    else:
        return True


async def apply_filter_rule(data: dict, token: str):
    rule_names = await ASYNC_REDIS.keys(f"rules:{token}:*")
    contents = list(search_value(data, "content"))

    # 过滤时间
    contents = [content for content in contents if "时间" not in content]

    # 过滤最近发送的内容
    msg_hash = hashlib.md5(json.dumps(contents).encode()).hexdigest()
    cache_key = f"feishu:{msg_hash}"

    if not await ASYNC_REDIS.set(cache_key, "sent", ex=settings.rules.feishu_same_message_interval, nx=True):
        LOG.warning(f"相同消息 60 秒内不重复发送")
        return False

    for rule_name in rule_names:
        rule_data = await ASYNC_REDIS.get(rule_name)
        rule = FilterRule.model_validate_json(rule_data)
        if not (apply_include(contents, rule.include) and apply_exclude(contents, rule.exclude)):
            return False
    return True


@feishu_router.post("/send/{token}")
async def send(token: str, request: Request):
    json_data = await request.json()
    LOG.info(f"请求参数: {token} {json_data = }")

    # 过滤
    if await apply_filter_rule(data=json_data, token=token):
        response = requests.post(
            url=f"https://open.feishu.cn/open-apis/bot/v2/hook/{token}",
            json=json_data,
        )
        LOG.info(response.json())
        return response.json()
    else:
        return {'StatusCode': 0, 'StatusMessage': 'success', 'code': 0, 'data': {}, 'msg': 'success'}


@feishu_router.post("/config/{token}")
async def configure_filter(token: str, rule: FilterRule):
    """添加新的过滤规则"""
    rule_data = json.dumps(rule.model_dump(exclude={"expires"}))
    # 计算 rule_id
    rule_id = hashlib.md5(rule_data.encode()).hexdigest()
    rule_name = f"rules:{token}:{rule_id}"
    # 添加规则
    await ASYNC_REDIS.set(
        name=rule_name,
        value=rule_data,
        ex=rule.expires or None
    )
    return {"rule_id": rule_id}


@feishu_router.delete("/config/{token}")
async def delete_filter(token: str, rule_id: Optional[str] = None):
    """删除过滤规则"""
    if rule_id is None:
        # 删除所有规则
        rule_names = await ASYNC_REDIS.keys(f"rules:{token}:*")
        for rule_name in rule_names:
            LOG.warning(f"删除规则 {rule_name}")
            await ASYNC_REDIS.delete(rule_name)
    else:
        # 删除指定规则
        rule_name = f"rules:{token}:{rule_id}"
        LOG.warning(f"删除规则 {rule_name}")
        await ASYNC_REDIS.delete(rule_name)

    return {"message": "success"}
