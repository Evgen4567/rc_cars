import logging
from http import HTTPStatus
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse

from src.managers import CarPoolManager
from src.routes.dependencies import broadcast, get_car_pool_manager

logger = logging.getLogger(__name__)
html = (Path(__file__).parent.parent.parent / "client.html").read_text(encoding='utf-8')
html_lobby = (Path(__file__).parent.parent.parent / "lobby.html").read_text(encoding='utf-8')

rest_router = APIRouter()


@rest_router.get("/")
async def index() -> HTMLResponse:
    return HTMLResponse(html)
@rest_router.get("/lobby")
async def index() -> HTMLResponse:
    return HTMLResponse(html_lobby, media_type="text/html; charset=utf-8")


@rest_router.get("/client")
async def client() -> HTMLResponse:
    return HTMLResponse(html)


@rest_router.get("/car_pool")
async def car_pool(car_pool_manager: Annotated[CarPoolManager, Depends(get_car_pool_manager)]) -> dict[str, str | None]:
    return car_pool_manager.car_owner_pool


@rest_router.get("/observer/{car_id}")
async def observer(
    car_id: str,
    car_pool_manager: Annotated[CarPoolManager, Depends(get_car_pool_manager)],
) -> StreamingResponse:
    # if car_id not in car_pool_manager.car_owner_pool:
    #     raise HTTPException(status_code=HTTPStatus.NOT_FOUND)
    return StreamingResponse(broadcast(car_id))
