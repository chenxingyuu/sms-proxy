import base64
import hashlib
import json
from typing import Dict, List, Union

import requests

from cores.config import settings
from cores.log import LOG


class CMCCMasSMS:
    """
    中国移动MAS短信平台API封装
    """

    def __init__(self, app_id, secret_key, ec_name, api_url, sign):
        self.app_id = app_id
        self.secret_key = secret_key
        self.ec_name = ec_name
        self.api_url = api_url
        self.sign = sign

    def generate_signature(self, data):
        """
        生成签名 将ecName、apId、secretKey、mobiles、content、sign、addSerial按序拼接（无间隔符），通过MD5（32位小写）计算得出值。
        """
        raw_string = (
            f"{self.ec_name}{self.app_id}{self.secret_key}{data['mobiles']}{data['content']}{data['sign']}{data['addSerial']}"
        )
        return hashlib.md5(raw_string.encode("utf-8")).hexdigest()

    def send_sms(self, phone_numbers: Union[List[str], str], message: Union[Dict, str], add_serial: str = ""):
        """
        发送短信
        :param phone_numbers: 接收短信的手机号（支持多个，用逗号分隔）
        :param message: 短信内容
        :param add_serial: 扩展码，可选
        :return: 请求响应
        >>> MasSMS.send_sms("15259616715", "您的验证码是123456")
        {'message': 'NOT_WHITE_IP', 'success': False}
        """
        payload = {
            "ecName": self.ec_name,
            "apId": self.app_id,
            "mobiles": phone_numbers if isinstance(phone_numbers, str) else ",".join(phone_numbers),
            "content": message if isinstance(message, str) else json.dumps({"content": message}, ensure_ascii=False),
            "sign": self.sign,
            "addSerial": add_serial,
        }
        signature = self.generate_signature(payload)
        payload["mac"] = signature
        LOG.info(json.dumps(payload, ensure_ascii=False))
        encode = base64.b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode("utf-8")
        try:
            response = requests.post(f"{self.api_url}", json=encode, verify=False, timeout=5)
            response_data = response.json() if response.status_code == 200 else {}
            if not response_data.get("success", False):
                raise Exception(f"短信发送失败: {response_data}")
            else:
                LOG.info(f"短信发送成功: {response_data}")

        except requests.RequestException as e:
            LOG.exception(f"发送短信时发生网络异常: {e}")
            raise e
        except Exception as e:
            LOG.exception(f"发送短信时发生未知异常: {e}")
            raise e


MasSMS = CMCCMasSMS(
    app_id=settings.mas.app_id,
    secret_key=settings.mas.secret_key,
    ec_name=settings.mas.ec_name,
    api_url=settings.mas.api_url,
    sign=settings.mas.sign
)
