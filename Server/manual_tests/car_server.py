import asyncio
import time
from datetime import UTC, datetime

from src.contracts import CarSignal
from websockets.asyncio.server import ServerConnection, serve

NANO_KOEF = 1_000_000_000
car_signal = CarSignal(moving=0, power=0, direction=0)
CAR_SIGNAL_BYTES = car_signal.pack()
CAR_SIGNAL_SIZE = len(CAR_SIGNAL_BYTES)


async def consumer_handler(websocket: ServerConnection):
    count_messages = 0
    message_size_total = 0
    max_message_size = 0
    min_message_size = 0
    start_time_ns = time.monotonic_ns()
    async for message in websocket:
        # читаем картинки но не печатаем в лог
        count_messages += 1
        current_time_ns = time.monotonic_ns()
        msg_size = len(message)
        message_size_total += msg_size
        max_message_size = max(msg_size, max_message_size)
        min_message_size = min(msg_size, min_message_size)

        if (current_time_ns - start_time_ns) <= 1 * NANO_KOEF:
            continue

        start_time_ns = current_time_ns
        dt = datetime.now(tz=UTC)
        print(f"{dt}: {count_messages=}\n{message_size_total=}\n{max_message_size=}\n{min_message_size=}")
        count_messages = 0
        message_size_total = 0
        max_message_size = 0
        min_message_size = 0


async def producer_handler(websocket: ServerConnection):
    start_time_ns = time.monotonic_ns()
    try:
        while True:
            current_time_ns = time.monotonic_ns()
            if (current_time_ns - start_time_ns) > 0.1 * NANO_KOEF:
                start_time_ns = current_time_ns
                start_send_ns = time.monotonic_ns()
                await websocket.send(CAR_SIGNAL_BYTES)
                send_duration = time.monotonic_ns() - start_send_ns
                dt = datetime.now(tz=UTC)
                print(f"{dt}: SEND BYTES: {send_duration=}, {CAR_SIGNAL_SIZE=}")
            await asyncio.sleep(0.0025)
    except Exception as e:
        print(e)


async def handler(websocket: ServerConnection):
    # https://websockets.readthedocs.io/en/stable/howto/patterns.html#consumer-and-producer
    consumer_task = asyncio.create_task(consumer_handler(websocket))
    producer_task = asyncio.create_task(producer_handler(websocket))
    done, pending = await asyncio.wait(
        [consumer_task, producer_task],
        return_when=asyncio.FIRST_COMPLETED,
    )
    for task in pending:
        task.cancel()


async def main():
    async with serve(handler, "0.0.0.0", 8000) as server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
