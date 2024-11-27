import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from src.managers import CarPoolManager
from src.routes.dependencies import get_car_pool_manager

logger = logging.getLogger(__name__)
html = (Path(__file__).parent.parent.parent / "client.html").read_text()

rest_router = APIRouter()


@rest_router.get("/")
async def index() -> HTMLResponse:
    return HTMLResponse(html)


@rest_router.get("/front")
async def front() -> HTMLResponse:
    return HTMLResponse(html)


@rest_router.get("/car_pool")
async def car_pool(car_pool_manager: Annotated[CarPoolManager, Depends(get_car_pool_manager)]) -> dict[str, str | None]:
    return car_pool_manager.car_owner_pool
