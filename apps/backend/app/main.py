from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine
from app import models


@asynccontextmanager
async def lifespan(app: FastAPI):
    models.Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="o1-agent", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}
