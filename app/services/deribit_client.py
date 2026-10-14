import aiohttp


class DeribitClient:
    def __init__(self, base_url: str):
        self.base_url = base_url

    async def get_index_price(self, ticker:str) -> float:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}{ticker}") as response:
                data = await response.json()

            return data["result"]["index_price"]