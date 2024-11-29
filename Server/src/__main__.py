import uvicorn

from src.application import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, timeout_keep_alive=60)  # noqa: S104
