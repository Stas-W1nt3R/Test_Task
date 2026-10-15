from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.repositories.price_repository import PriceRepository
from app.schemas.price import PriceRead
from datetime import date, datetime, time, timezone


router = APIRouter()

@router.get("/prices/all", response_model=list[PriceRead])
async def get_all_prices(ticker: str, db: AsyncSession = Depends(get_db)):
    repository = PriceRepository(db)
    return await repository.get_all_by_ticker(ticker)

@router.get("/prices/last", response_model=PriceRead)
async def get_last_price(ticker: str, db: AsyncSession = Depends(get_db)):
    repository = PriceRepository(db)
    return await repository.get_last_price(ticker)

@router.get("/prices/date", response_model=list[PriceRead])
async def get_price_by_date(ticker: str, date: date, db: AsyncSession = Depends(get_db)):
    repository = PriceRepository(db)
    start_date = int(datetime.combine(date, time.min, tzinfo=timezone.utc).timestamp())
    end_date = int(datetime.combine(date, time.max, tzinfo=timezone.utc).timestamp())
    return await repository.get_price_by_ticker_btw_date(ticker, start_date, end_date)