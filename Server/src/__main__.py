import asyncio
from contextlib import asynccontextmanager
import logging
from pathlib import Path
from typing import Callable, Coroutine
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn
from src.managers import WebsocketManager, CarPoolManager, TransferManager
from src.contracts import CarSignal, CarTelemetry, ClientSignal, ClientTelemetry, repack

logger = logging.getLogger(__name__)
html = Path("src/client.html").read_text()
car_manager = WebsocketManager()
client_manager = WebsocketManager()
car_pool_manager = CarPoolManager()
transfer_manager = TransferManager(car_manager=car_manager, client_manager=client_manager)
background_tasks = set()
SLEEP_UPDATE_CARS_TIME = 1.0
SIGNALS_SEND_SLEEP = 0.000001
TELEMETRY_SEND_SLEEP = 0.000001

async def update_cars_loop() -> None:
    while True:
        all_cars_ids = list(car_manager.active_connections.keys())
        car_pool_manager.update_available_cars(all_cars_ids)
        await asyncio.sleep(SLEEP_UPDATE_CARS_TIME)

async def handle_signals_loop() -> None:
    while True:
        await transfer_manager.handle_signals()
        await asyncio.sleep(SIGNALS_SEND_SLEEP)

async def handle_telemetry_loop() -> None:
    while True:
        await transfer_manager.handle_telemetry()
        await asyncio.sleep(TELEMETRY_SEND_SLEEP)

def add_loop_task(func: Callable) -> None:
    task = asyncio.create_task(func())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)

@asynccontextmanager
async def lifespan(app: FastAPI):
    add_loop_task(update_cars_loop)
    add_loop_task(handle_signals_loop)
    add_loop_task(handle_telemetry_loop)
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/car/{car_id}")
async def websocket_endpoint(websocket: WebSocket, car_id: str):
    await car_manager.connect(websocket, car_id)
    try:
        while True:
            telemetry = await car_manager.receive(car_id, CarTelemetry)
            if not (client_id := car_pool_manager.car_owner_pool.get(car_id)):
                continue
            client_telemetry = repack(telemetry, ClientTelemetry)
            await transfer_manager.add_telemetry(client_telemetry, client_id)
    except WebSocketDisconnect:
        car_manager.disconnect(car_id)

@app.websocket("/client/{client_id}/{car_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, car_id):
    await client_manager.connect(websocket, client_id)
    car_pool_manager.assign_car(client_id, car_id)
    logger.info(f"Client join: {client_id=}")
    try:
        while True:
            client_signal = await client_manager.receive(client_id, ClientSignal)
            if not (_car_id := car_pool_manager.owner_car_pool.get(client_id)):
                continue
            car_signal = repack(client_signal, CarSignal)
            await transfer_manager.add_signal(car_signal, _car_id)
    except WebSocketDisconnect:
        client_manager.disconnect(client_id)
        car_pool_manager.release_car(car_id, client_id)
        logger.info(f"Client #{client_id} left")


if __name__ == "__main__":
    uvicorn.run(app)
