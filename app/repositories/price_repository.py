from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import PriceRecord


class PriceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, ticker: str, price: float, timestamp: int) -> PriceRecord:
        record = PriceRecord(ticker=ticker, current_price=price, time=timestamp)
        self.session.add(record)
        await self.session.commit()
        return record

    async def get_all_by_ticker(self, ticker: str) -> list[PriceRecord]:
        result = await self.session.execute(
            select(PriceRecord).where(PriceRecord.ticker == ticker)
        )
        return result.scalars().all()

    async def get_last_price(self, ticker: str) -> PriceRecord | None:
        result = await self.session.execute(
            select(PriceRecord).where(PriceRecord.ticker == ticker).order_by(PriceRecord.time.desc()).limit(1)
        )
        return result.scalars().first()

    async def get_price_by_ticker_btw_date(self, ticker: str,start_date: int, end_date: int) -> list[PriceRecord]:
        result = await self.session.execute(
            select(PriceRecord).where(PriceRecord.ticker == ticker, PriceRecord.time.between(start_date, end_date))
        )
        return result.scalars().all()
