import asyncio
from collections.abc import AsyncGenerator, Callable, Coroutine
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.managers import CarPoolManager, LobbyManager, WebsocketManager

car_manager = WebsocketManager()
client_manager = WebsocketManager()
car_pool_manager = CarPoolManager(sleep_update_cars_seconds=1.0)
lobby_manager = LobbyManager()
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


def get_lobby_manager() -> LobbyManager:
    return lobby_manager
