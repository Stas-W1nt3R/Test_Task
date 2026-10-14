from app.core.celery_app import app
from app.services.deribit_client import DeribitClient
from app.repositories.price_repository import PriceRepository
from app.db.session import SessionLocal, engine
from app.core.config import settings
import asyncio
import time

@app.task(name='fetch_prices')
def fetch_prices():
    asyncio.run(fetch_prices_async())

async def fetch_prices_async():
    client = DeribitClient(base_url=settings.deribit_api_url)
    async with SessionLocal() as session:
        repository = PriceRepository(session)
        for ticker in ["btc_usd", "eth_usd"]:
            price = await client.get_index_price(ticker)
            await repository.add(ticker=ticker, price=price, timestamp=int(time.time()))

    await engine.dispose()