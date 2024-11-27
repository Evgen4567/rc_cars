import logging

from fastapi import FastAPI

from src.routes.dependencies import lifespan
from src.routes.rest import rest_router
from src.routes.ws import ws_router

logger = logging.getLogger(__name__)


app = FastAPI(lifespan=lifespan)
app.include_router(ws_router)
app.include_router(rest_router)
