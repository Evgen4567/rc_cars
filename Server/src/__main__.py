import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import uvicorn
from src.managers import CarManager

logger = logging.getLogger(__name__)
app = FastAPI()
html = Path("src/client.html").read_text()
car_manager = CarManager()

@app.get("/")
async def get():
    return HTMLResponse(html)


@app.websocket("/car/{car_id}")
async def websocket_endpoint(websocket: WebSocket, car_id: str):
    await car_manager.connect(websocket, car_id)
    # TODO add car to <free car list>
    try:
        while True:
            telemetry = await car_manager.receive_telemetry(car_id)
            print(telemetry)
            # TODO check - get client binded to car
            # TODO if client - send data to him
                # TODO get message from client to car
                # TODO if message - send message to car
    except WebSocketDisconnect:
        car_manager.disconnect(websocket)


if __name__ == "__main__":
    uvicorn.run(app)
