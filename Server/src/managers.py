import logging
from fastapi import WebSocket
from src.contracts import CarSignal, CarTelemetry, pack, unpack

logger = logging.getLogger(__name__)

class CarManager:
    def __init__(self) -> None:
        self.active_connections: dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, car_id: str):
        # TODO validate that car is our car
        await websocket.accept()
        self.active_connections[car_id] = websocket

    def disconnect(self, car_id: str):
        del self.active_connections[car_id]

    def _get_car_websocket(self, car_id: str) -> WebSocket:
        if not (websocket := self.active_connections.get(car_id)):
            raise Exception("WTF: where is car websocket?")
        return websocket
    
    async def receive_telemetry(self, car_id: str) -> CarTelemetry:
        websocket = self._get_car_websocket(car_id)
        bytes_data = await websocket.receive_bytes()
        telemetry = unpack(bytes_data, CarTelemetry)
        return telemetry
    
    async def send_signal(self, car_id: str, car_signal: CarSignal) -> None:
        data = pack(car_signal)
        websocket = self._get_car_websocket(car_id)
        await websocket.send_bytes(data)
