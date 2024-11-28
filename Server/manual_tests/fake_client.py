import asyncio
import random

import websockets
from src.contracts import CarSignal


def generate_signal() -> bytes:
    moving = random.choice((1, 0, -1, 9))
    power = random.randint(0, 1024)
    direction = random.randint(-1024, 1024)

    telemetry = CarSignal(moving, power, direction)
    return telemetry.pack()


async def read_messages(websocket) -> None:  # type: ignore[no-untyped-def] # noqa:ANN001
    async for message in websocket:
        print(f"Received: {message}")  # noqa: T201


async def send_messages(websocket, object_id) -> None:  # type: ignore[no-untyped-def] # noqa:ANN001, ARG001
    while True:
        msg = generate_signal()
        await websocket.send(msg)
        await asyncio.sleep(0.01)


async def start_lobby_observer(client_name: str) -> None:
    uri = f"ws://127.0.0.1:8000/lobby/{client_name}"
    async with websockets.connect(uri) as websocket:
        await read_messages(websocket)


async def run_lobby_ws_connection() -> None:
    tasks = [start_lobby_observer(f"observer_{i}") for i in range(10)]
    await asyncio.gather(*tasks)


async def main() -> None:
    background_tasks = set()
    task: asyncio.Task[None] = asyncio.create_task(run_lobby_ws_connection())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)
    client_id = "fake_client"
    car_id = "fake_car_0"
    uri = f"ws://127.0.0.1:8000/client/{client_id}/{car_id}"
    async with websockets.connect(uri) as websocket:
        await asyncio.gather(read_messages(websocket), send_messages(websocket, client_id))


asyncio.run(main())
