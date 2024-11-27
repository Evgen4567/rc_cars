import asyncio
import logging

from fastapi import WebSocket

from src.contracts import A

logger = logging.getLogger(__name__)


class WebsocketManager:
    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}

    def _get_object_websocket(self, object_id: str) -> WebSocket:
        if not (websocket := self.active_connections.get(object_id)):
            msg = f"WTF: where is {object_id=} websocket?"
            raise RuntimeError(msg)
        return websocket

    async def connect(self, websocket: WebSocket, object_id: str) -> None:
        await websocket.accept()
        self.active_connections[object_id] = websocket

    def disconnect(self, object_id: str) -> None:
        del self.active_connections[object_id]

    async def receive(self, object_id: str, expect_data_type: type[A]) -> A:
        websocket = self._get_object_websocket(object_id)
        bytes_data = await websocket.receive_bytes()
        return expect_data_type.unpack(bytes_data)

    async def send(self, object_id: str, contract: A) -> None:
        data = contract.pack()
        websocket = self._get_object_websocket(object_id)
        await websocket.send_bytes(data)


class CarPoolManager:
    def __init__(self, sleep_update_cars_seconds: float):
        self.car_owner_pool: dict[str, str | None] = {}
        self.owner_car_pool: dict[str, str] = {}
        self.sleep_update_cars_seconds = sleep_update_cars_seconds

    def add_car(self, car_id: str, owner_id: str | None = None) -> None:
        """Добавить новую машину в пул. Если нет владельца, то она свободна."""
        self.car_owner_pool[car_id] = owner_id
        if owner_id:
            self.owner_car_pool[owner_id] = car_id

    def assign_car(self, client_id: str, car_id: str) -> bool:
        """Назначить машину клиенту, если она свободна и принадлежит клиенту."""
        if car_id not in self.car_owner_pool:
            msg = f"Машина {car_id} не существует в пуле."
            raise ValueError(msg)

        if self.car_owner_pool[car_id] is not None:
            msg = f"Машина {car_id} уже занята."
            raise RuntimeError(msg)

        self.car_owner_pool[car_id] = client_id
        self.owner_car_pool[client_id] = car_id
        return True

    def release_car(self, car_id: str, owner_id: str) -> None:
        """Освободить машину, удалив владельца."""
        if car_id in self.car_owner_pool:
            self.car_owner_pool[car_id] = None
        if owner_id in self.owner_car_pool:
            del self.owner_car_pool[owner_id]

    def get_available_cars(self) -> list[str]:
        """Получить список свободных машин (где нет владельца)."""
        return [car_id for car_id, owner_id in self.car_owner_pool.items() if owner_id is None]

    async def update_available_cars(self, external_car_list: list[str]) -> None:
        """Обновить список доступных машин из внешнего источника."""
        for car_id in external_car_list:
            if car_id not in self.car_owner_pool:
                self.add_car(car_id)
        car_pool = list(self.car_owner_pool.keys())
        for car_id in car_pool:
            if car_id not in external_car_list:
                del self.car_owner_pool[car_id]
        await asyncio.sleep(self.sleep_update_cars_seconds)
