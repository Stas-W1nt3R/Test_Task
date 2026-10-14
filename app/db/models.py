from sqlalchemy.orm import mapped_column, Mapped
from app.db.base import Base

class PriceRecord(Base):
    __tablename__ = 'price_record'

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(index=True)
    current_price: Mapped[float]
    time: Mapped[int]