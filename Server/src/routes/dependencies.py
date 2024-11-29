import asyncio
import os
from collections.abc import AsyncGenerator, Callable, Coroutine
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import Redis

from src.managers import CarPoolManager, WebsocketManager

car_manager = WebsocketManager()
client_manager = WebsocketManager()
car_pool_manager = CarPoolManager(sleep_update_cars_seconds=1.0)
redis_client = Redis(host=os.getenv("REDIS_HOST", "localhost"), port=int(os.getenv("REDIS_PORT", "6379")))
background_tasks = set()


async def update_cars_loop() -> None:
    while True:
        all_cars_ids = list(car_manager.active_connections.keys())
        await car_pool_manager.update_available_cars(all_cars_ids)


def add_loop_task(func: Callable[[], Coroutine[None, None, None]]) -> None:
    task: asyncio.Task[None] = asyncio.create_task(func())
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:  # noqa: ARG001
    add_loop_task(update_cars_loop)
    yield


def get_car_manager() -> WebsocketManager:
    return car_manager


def get_client_manager() -> WebsocketManager:
    return client_manager


def get_car_pool_manager() -> CarPoolManager:
    return car_pool_manager


def get_redis_stream_client() -> Redis:
    return redis_client


async def broadcast(car_id: str) -> AsyncGenerator[bytes, None]:
    stream = redis_client.pubsub(ignore_subscribe_messages=True)
    await stream.subscribe(car_id)
    async for message in stream.listen():
        yield message["data"]
