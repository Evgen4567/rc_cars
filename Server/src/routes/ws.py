import logging
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from redis.asyncio import Redis

from src.contracts import CarSignal, CarTelemetry, ClientSignal, ClientTelemetry, repack
from src.managers import CarPoolManager, WebsocketManager
from src.routes.dependencies import get_car_manager, get_car_pool_manager, get_client_manager, get_redis_stream_client

logger = logging.getLogger(__name__)
ws_router = APIRouter()


@ws_router.websocket("/car/{car_id}")
async def car(
    websocket: WebSocket,
    car_id: str,
    car_manager: Annotated[WebsocketManager, Depends(get_car_manager)],
    car_pool_manager: Annotated[CarPoolManager, Depends(get_car_pool_manager)],
    stream_client: Annotated[Redis, Depends(get_redis_stream_client)],
    client_manager: Annotated[WebsocketManager, Depends(get_client_manager)],
) -> None:
    await car_manager.connect(websocket, car_id)
    try:
        while True:
            telemetry = await car_manager.receive(car_id, CarTelemetry)
            client_telemetry = repack(telemetry, ClientTelemetry)
            await stream_client.publish(car_id, client_telemetry.pack())
            if not (client_id := car_pool_manager.car_owner_pool.get(car_id)):
                continue
            await client_manager.send(client_id, client_telemetry)

    except WebSocketDisconnect:
        car_manager.disconnect(car_id)


@ws_router.websocket("/client/{client_id}/{car_id}")
async def client_car(
    websocket: WebSocket,
    client_id: str,
    car_id: str,
    car_manager: Annotated[WebsocketManager, Depends(get_car_manager)],
    car_pool_manager: Annotated[CarPoolManager, Depends(get_car_pool_manager)],
    client_manager: Annotated[WebsocketManager, Depends(get_client_manager)],
) -> None:
    await client_manager.connect(websocket, client_id)
    car_pool_manager.assign_car(client_id, car_id)
    logger.info(f"Client join: {client_id=}")  # noqa: G004
    try:
        while True:
            client_signal = await client_manager.receive(client_id, ClientSignal)
            if not (_car_id := car_pool_manager.owner_car_pool.get(client_id)):
                continue
            car_signal = repack(client_signal, CarSignal)
            await car_manager.send(_car_id, car_signal)
    except WebSocketDisconnect:
        client_manager.disconnect(client_id)
        car_pool_manager.release_car(car_id, client_id)
        logger.info(f"Client #{client_id} left")  # noqa: G004
