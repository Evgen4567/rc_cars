import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn
from src.managers import WebsocketManager
from src.contracts import CarSignal, CarTelemetry, ClientSignal, ClientTelemetry

logger = logging.getLogger(__name__)
app = FastAPI()
html = Path("src/client.html").read_text()
car_manager = WebsocketManager()
client_manager = WebsocketManager()

@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/car/{car_id}")
async def websocket_endpoint(websocket: WebSocket, car_id: str):
    await car_manager.connect(websocket, car_id)
    # TODO добавить в список машин, готовых обслуживать клиентов ^_^
    try:
        while True:
            telemetry = await car_manager.receive(car_id, CarTelemetry)
            print(telemetry)
            # TODO получить клиента, которого обслуживает машина
            # TODO отправить клиенту телеметрию
            # TODO получить сигнал от клинент
            # TODO отправить сигнал машинке
    except WebSocketDisconnect:
        car_manager.disconnect(websocket)

@app.websocket("/client/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await client_manager.connect(websocket, client_id)
    logger.info(f"Client join: {client_id=}")
    try:
        while True:
            client_signal = await client_manager.receive(client_id, ClientSignal)
            print(client_signal)
            # TODO положить сигнал куда-то, чтобы потом отправить машинке
            # TODO получить телеметрию для клиента
            # TODO отправить телеметрию клиенту
    except WebSocketDisconnect:
        client_manager.disconnect(websocket)
        logger.info(f"Client #{client_id} left")


if __name__ == "__main__":
    uvicorn.run(app)
