import contextlib
import importlib
import pkgutil
from typing import AsyncIterator

from fastapi import FastAPI
from ghkit.log import setup_logging
from starlette.middleware.cors import CORSMiddleware

from cores.config import settings
from cores.log import LOG
from cores.sio import attach_socketio


def register_routes(_app: FastAPI):
    LOG.info("Scanning and registering routes...")

    # 扫描 `app` 目录下所有子模块（假设 `app` 目录下的 `urls.py` 里有 `router`）
    package_name = "app"
    for finder, name, is_pkg in pkgutil.iter_modules([package_name.replace(".", "/")]):
        module_name = f"{package_name}.{name}.urls"
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, "router"):
                _app.include_router(module.router, prefix=settings.app.api_version)
                LOG.debug(f"Registered router from {module_name}")
        except ModuleNotFoundError:
            LOG.warning(f"No URLs found in {module_name}, skipping...")

    LOG.info("All routes registered.")


def check_redis():
    LOG.info("Checking Redis connection...")
    try:
        from cores.redis import REDIS
        REDIS.ping()
    except Exception as e:
        LOG.error(f"Redis connection failed: {e}")
        raise e
    LOG.info("Redis connection OK.")


@contextlib.asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    LOG.info("Starting application lifespan...")
    # 应用启动时的初始化

    # 注册路由
    register_routes(_app)

    # 检查 Redis
    check_redis()

    # 注册 Socket.IO
    attach_socketio(_app)

    # 通过 yield 将控制权交给 FastAPI
    yield


def make_app():
    setup_logging()  # 启用 loguru 作为全局日志系统
    app = FastAPI(
        title=settings.app.project_name,
        debug=settings.app.debug,
        lifespan=lifespan,
        docs_url=settings.app.doc_path,
        redoc_url=None,
        openapi_url=f"{settings.app.doc_path}.json",
    )
    # 添加 CORS 中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 允许所有来源
        allow_credentials=True,
        allow_methods=["*"],  # 允许所有方法
        allow_headers=["*"],  # 允许所有头部
    )
    return app
