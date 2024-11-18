from fastapi import FastAPI
from src.bot import Bot

from contextlib import asynccontextmanager

@asynccontextmanager
def lifespan(app: FastAPI):
    Bot().startBot()

app = FastAPI(lifespan=lifespan)