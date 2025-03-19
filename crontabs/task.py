import json
import time

import schedule

from cores.log import LOG
from cores.redis import REDIS
from cores.sms import MasSMS
from crontabs.base import BaseScript


class MasTask(BaseScript):
    schedule_job = schedule.every(5).seconds

    def __call__(self, *args, **kwargs):
        """
        每 5 秒消费 Redis 队列的短信，并批量发送
        msg_hash = hashlib.md5(f"{message.phone_number}_{message.message}".encode()).hexdigest()
        cache_key = f"mas:sms:{msg_hash}"

        if not await ASYNC_REDIS.set(cache_key, "sent", ex=60, nx=True):
            LOG.warning(f"相同短信 60 秒内不重复发送 {message = }")
            continue
        """
        sms_batch = []

        while len(sms_batch) < 100:  # 限制一次最多批量100条短信
            sms_data = REDIS.rpop("sms_queue")
            if not sms_data:
                break
            sms_batch.append(json.loads(sms_data))

        LOG.info(f"获取到短信队列: {sms_batch}")

        if sms_batch:
            messages = {
                sms["phone_number"]: sms["message"] for sms in sms_batch
            }
            phone_numbers = list(messages.keys())
            if len(phone_numbers) == 1:
                LOG.info(f"单条发送短信: {messages}")
                MasSMS.send_sms(phone_numbers[0], messages[phone_numbers[0]])
            else:
                LOG.info(f"批量发送短信: {messages}")
                MasSMS.send_sms(phone_numbers, messages)


def main():
    script = MasTask()
    script()

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    main()
