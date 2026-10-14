from fastapi import FastAPI
from app.api.prices import router
from contextlib import asynccontextmanager
from app.db.base import Base
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title='Deribit price tracker', lifespan=lifespan)
app.include_router(router)
