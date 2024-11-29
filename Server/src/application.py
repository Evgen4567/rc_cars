import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.routes.dependencies import lifespan
from src.routes.rest import rest_router
from src.routes.ws import ws_router

logger = logging.getLogger(__name__)


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Лучше ограничить допустимые источники
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ws_router)
app.include_router(rest_router)
