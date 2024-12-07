import asyncio
from itertools import cycle
import os
import pickle
import time
from datetime import UTC, datetime
from typing import Generator
from websockets.asyncio.client import connect


from src.contracts import CarSignal, CarTelemetry
from websockets.asyncio.server import ServerConnection, serve

NANO_KOEF = 1_000_000_000
car_signal = CarSignal(moving=0, power=0, direction=0)
CAR_SIGNAL_BYTES = car_signal.pack()
CAR_SIGNAL_SIZE = len(CAR_SIGNAL_BYTES)

data_path = "./.vscode/telemetry.pkl"

def sinthetic_stream(frame_size: int) -> Generator[bytes, None, None]:
    while True:
        telemetry = CarTelemetry(
            frame=os.urandom(frame_size), 
            battery=0, 
            speed=0, 
            power=0, 
            name="test"
        )
        yield telemetry.pack()

async def _consume(websocket: ServerConnection):
    async for message in websocket:
        ...

async def _produce(websocket: ServerConnection, sleep_time: float, frame_size: int):
    for message in sinthetic_stream(frame_size):
        await websocket.send(message)
        await asyncio.sleep(sleep_time)


async def main():
    # ----------------
    FRAME_SIZE = 32 * 1024
    FPS = 50
    #-----------------
    sleep_time = round(1 / FPS, 4)
    async with connect("ws://localhost:8000") as websocket:
        consumer_task = asyncio.create_task(_consume(websocket))
        producer_task = asyncio.create_task(_produce(websocket, sleep_time, FRAME_SIZE))
        done, pending = await asyncio.wait(
            [consumer_task, producer_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()


if __name__ == "__main__":
    asyncio.run(main())