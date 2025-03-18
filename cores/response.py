from typing import Generic, Optional, TypeVar

from ghkit.enum import GEnum
from pydantic import BaseModel

T = TypeVar("T")


class ResponseCode(GEnum):
    SUCCESS = 20000, "Success"
    CLIENT_ERROR = 40000, "Error"


class ResponseModel(BaseModel, Generic[T]):
    code: ResponseCode = ResponseCode.SUCCESS
    msg: str = code.desc
    data: Optional[T] = None


class ResponseErrorModel(BaseModel):
    code: ResponseCode = ResponseCode.CLIENT_ERROR
    msg: str = code.desc
    data: Optional[dict] = None
