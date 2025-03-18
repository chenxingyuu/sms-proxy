import uvicorn

from cores.config import settings
from cores.fastapi_app import make_app

app = make_app()

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.app.host,
        port=settings.app.port,
        reload=settings.app.debug,
        log_config=None,
    )
