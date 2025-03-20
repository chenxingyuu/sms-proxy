import asyncio
import os
import traceback

import schedule
import socketio
from schedule import Job

from cores.config import settings
from cores.log import LOG
from cores.messager import MESSAGE_FACTORY

redis_manager = socketio.AsyncRedisManager(settings.redis.db_url)
sio = socketio.AsyncServer(client_manager=redis_manager)


class ScriptMeta(type):
    """
    脚本元类
    1. 用于捕获脚本执行过程中的异常
    2. 用于执行定时任务

    """

    def __new__(cls, name, bases, dct):
        # 获取 __call__ 方法
        original_call = dct.get("__call__")

        if asyncio.iscoroutinefunction(original_call):  # 判断是否是异步函数
            async def new_call(self, *args, **kwargs):
                try:
                    # 获取 schedule_job
                    if schedule_job := kwargs.pop("schedule_job", None) or getattr(self, "schedule_job", None):
                        # 防止 schedule_job 被重复调用
                        setattr(self, "schedule_job", None)
                        assert isinstance(schedule_job, Job), "schedule_job 必须是 schedule.Job 类型"

                        # 添加定时任务，支持异步
                        async def wrapped_job():
                            await self(*args, **kwargs)

                        schedule_job.do(lambda: asyncio.create_task(wrapped_job()))

                    # 调用原始的 __call__ 方法
                    return await original_call(self, *args, **kwargs)
                except Exception as e:
                    # 捕获并处理异常
                    self.handle_exception(e, name)

        else:
            def new_call(self, *args, **kwargs):
                try:
                    # 获取 schedule_job
                    if schedule_job := kwargs.pop("schedule_job", None) or getattr(self, "schedule_job", None):
                        # 防止 schedule_job 被重复调用
                        setattr(self, "schedule_job", None)
                        assert isinstance(schedule_job, Job), "schedule_job 必须是 schedule.Job 类型"

                        # 添加定时任务
                        schedule_job.do(self, *args, **kwargs)

                    # 调用原始的 __call__ 方法
                    return original_call(self, *args, **kwargs)
                except Exception as e:
                    # 捕获并处理异常
                    self.handle_exception(e, name)

        # 替换原始 __call__ 方法
        dct["__call__"] = new_call

        # 创建类
        new_class = super().__new__(cls, name, bases, dct)
        return new_class


class BaseScript(metaclass=ScriptMeta):
    """脚本基类"""

    @classmethod
    def handle_exception(cls, _, class_name):
        error_stack = traceback.format_exc()
        device = os.uname().nodename
        # 飞书通知
        cls._feishu_alarm(class_name=class_name, stack=error_stack, device=device)

    @classmethod
    def _feishu_alarm(cls, class_name, stack, device):
        try:
            message_dict = {
                "config": {},
                "i18n_elements": {
                    "zh_cn": [
                        {
                            "tag": "markdown",
                            "content": f"**脚本：** {class_name}",
                            "text_align": "left",
                            "text_size": "normal",
                            "icon": {
                                "tag": "standard_icon",
                                "token": "lan_outlined",
                                "color": "grey"
                            }
                        },
                        {
                            "tag": "markdown",
                            "content": f"**服务器: {device}**",
                            "text_align": "left",
                            "text_size": "normal",
                            "icon": {
                                "tag": "standard_icon",
                                "token": "computer_outlined",
                                "color": "grey"
                            }
                        },
                        {
                            "tag": "markdown",
                            "content": stack,
                            "text_align": "left",
                            "text_size": "normal",
                            "icon": {
                                "tag": "standard_icon",
                                "token": "ram_outlined",
                                "color": "grey"
                            }
                        }
                    ]
                },
                "i18n_header": {
                    "zh_cn": {
                        "title": {"tag": "plain_text", "content": "🚨脚本异常🚨"},
                        "subtitle": {"tag": "plain_text", "content": ""},
                        "template": "blue",
                    }
                },
            }
            # 发送告警信息
            MESSAGE_FACTORY.send_alarm(message_dict)
        except Exception as e:
            LOG.exception(f"发送告警信息时发生错误: {e}")


class DemoAsyncScript(BaseScript):
    schedule_job = schedule.every(1).seconds

    async def async_init(self):
        """初始化任务"""
        LOG.info(f"Async init for {self.__class__.__name__}")
        await asyncio.sleep(1)  # 模拟异步初始化

    async def __call__(self, *args, **kwargs):
        """实际任务逻辑"""
        LOG.info("异步任务开始")
        await asyncio.sleep(1)
        LOG.info("异步任务结束")


async def main():
    script = DemoAsyncScript()

    await script.async_init()

    # 异步定时任务执行
    async def run_tasks():
        await script()
        while True:
            schedule.run_pending()
            await asyncio.sleep(1)  # 确保事件循环不会阻塞

    try:
        await run_tasks()
    except KeyboardInterrupt:
        LOG.info("Shutting down...")
    finally:
        LOG.info("Clean up and exit")


if __name__ == '__main__':
    asyncio.run(main())
