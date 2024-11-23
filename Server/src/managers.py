import logging
from typing import TypeVar
from fastapi import WebSocket
from src.contracts import pack, unpack, CarSignal, ClientTelemetry
from asyncio import Queue, QueueEmpty

logger = logging.getLogger(__name__)
T = TypeVar("T")

class WebsocketManager:
    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}

    def _get_object_websocket(self, object_id: str) -> WebSocket:
        if not (websocket := self.active_connections.get(object_id)):
            raise Exception(f"WTF: where is {object_id=} websocket?")
        return websocket

    async def connect(self, websocket: WebSocket, object_id: str):
        await websocket.accept()
        self.active_connections[object_id] = websocket

    def disconnect(self, object_id: str):
        del self.active_connections[object_id]

    async def receive(self, object_id: str, expect_data_type: type[T]) -> T:
        websocket = self._get_object_websocket(object_id)
        bytes_data = await websocket.receive_bytes()
        return unpack(bytes_data, expect_data_type)
    
    async def send(self, object_id: str, contract: T) -> None:
        data = pack(contract)
        websocket = self._get_object_websocket(object_id)
        await websocket.send_bytes(data)

class CarPoolManager:
    def __init__(self):
        self.car_owner_pool: dict[str, str | None] = {}
        self.owner_car_pool: dict[str, str] = {}

    def add_car(self, car_id: str, owner_id: str | None = None):
        """Добавить новую машину в пул. Если нет владельца, то она свободна."""
        self.car_owner_pool[car_id] = owner_id
        if owner_id:
            self.owner_car_pool[owner_id] = car_id

    def assign_car(self, client_id: str, car_id: str) -> bool:
        """Назначить машину клиенту, если она свободна и принадлежит клиенту."""
        if car_id not in self.car_owner_pool:
            raise ValueError(f"Машина {car_id} не существует в пуле.")
        
        if self.car_owner_pool[car_id] is not None:
            raise RuntimeError(f"Машина {car_id} уже занята.")
        
        self.car_owner_pool[car_id] = client_id
        self.owner_car_pool[client_id] = car_id
        return True

    def release_car(self, car_id: str, owner_id: str):
        """Освободить машину, удалив владельца."""
        if car_id in self.car_owner_pool:
            self.car_owner_pool[car_id] = None
        if owner_id in self.owner_car_pool:
            del self.owner_car_pool[owner_id]

    def get_available_cars(self):
        """Получить список свободных машин (где нет владельца)."""
        return [car_id for car_id, owner_id in self.car_owner_pool.items() if owner_id is None]

    def update_available_cars(self, external_car_list: list[str]):
        """Обновить список доступных машин из внешнего источника."""
        for car_id in external_car_list:
            if car_id not in self.car_owner_pool:
                self.add_car(car_id)
        car_pool = list(self.car_owner_pool.keys())
        for car_id in car_pool:
            if car_id not in external_car_list:
                del self.car_owner_pool[car_id]


class TransferManager:
    def __init__(self, car_manager: WebsocketManager, client_manager: WebsocketManager) -> None:
        self._signals_queue = Queue()
        self._telemetry_queue = Queue()
        self.car_manager = car_manager
        self.client_manager = client_manager

    async def add_signal(self, signal: CarSignal, car_id: str) -> None:
        await self._signals_queue.put((signal, car_id))

    async def add_telemetry(self, telemetry: ClientTelemetry, client_id: str) -> None:
        await self._telemetry_queue.put((telemetry, client_id))

    async def handle_signals(self) -> None:
        try:
            signal_packet: tuple[CarSignal, str] = self._signals_queue.get_nowait()
        except QueueEmpty:
            return
        signal, car_id = signal_packet
        await self.car_manager.send(car_id, signal)

    async def handle_telemetry(self) -> None:
        try:
            signal_packet: tuple[ClientTelemetry, str] = self._telemetry_queue.get_nowait()
        except QueueEmpty:
            return
        telemetry, client_id = signal_packet
        await self.client_manager.send(client_id, telemetry)