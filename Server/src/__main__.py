import os

import uvicorn

from src.application import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("SERVER_HOST", "0.0.0.0"),  # noqa: S104
        port=int(os.getenv("SERVER_PORT", "8000")),
        ws_max_queue=int(os.getenv("SERVER_WS_MAX_QUEUE", "256")),
        ws_max_size=int(os.getenv("SERVER_WS_MAX_SIZE", "16777216")),
    )
