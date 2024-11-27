import asyncio
import random

import websockets
from src.contracts import CarTelemetry


def generate_telemetry(car_id: str) -> bytes:
    frame_length = random.randint(1000, 5000)
    frame_data = bytes(random.choices(range(256), k=frame_length))
    battery = random.randint(3500, 7800)
    speed = random.randint(1000, 10000)
    power = random.randint(5000, 15000)

    telemetry = CarTelemetry(frame_data, battery, speed, power, car_id)
    return telemetry.pack()


async def read_messages(websocket) -> None:  # type: ignore[no-untyped-def] # noqa:ANN001
    async for message in websocket:
        print(f"Received: {message}")  # noqa: T201


async def send_messages(websocket, car_id) -> None:  # type: ignore[no-untyped-def] # noqa:ANN001
    while True:
        msg = generate_telemetry(car_id)
        await websocket.send(msg)
        await asyncio.sleep(0.001)


async def main() -> None:
    car_id = "fake_car"
    uri = f"ws://127.0.0.1:8000/car/{car_id}"
    async with websockets.connect(uri) as websocket:
        await asyncio.gather(read_messages(websocket), send_messages(websocket, car_id))


asyncio.run(main())
