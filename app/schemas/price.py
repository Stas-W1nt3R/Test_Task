from pydantic import BaseModel, ConfigDict


class PriceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker: str
    current_price: float
    time: int
