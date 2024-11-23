import logging
from typing import TypeVar
from fastapi import WebSocket
from src.contracts import pack, unpack

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
