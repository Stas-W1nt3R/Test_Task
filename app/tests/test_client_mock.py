from unittest.mock import MagicMock, AsyncMock, patch
from app.services.deribit_client import DeribitClient
from app.core.config import settings
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import get_db
import unittest


class ClientMock(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = DeribitClient(base_url=settings.deribit_api_url)

    def fake_session(self, data):
        response = MagicMock()
        response.json = AsyncMock(return_value=data)

        get_cm = MagicMock()
        get_cm.__aenter__ = AsyncMock(return_value=response)
        get_cm.__aexit__ = AsyncMock(return_value=False)

        session = MagicMock()
        session.get = MagicMock(return_value=get_cm)

        client_session_cm = MagicMock()
        client_session_cm.__aenter__ = AsyncMock(return_value=session)
        client_session_cm.__aexit__ = AsyncMock(return_value=False)
        return client_session_cm

    async def test_get_index_price(self):
        session = self.fake_session({"result": {"index_price": 81700}})
        with patch("app.services.deribit_client.aiohttp.ClientSession", return_value=session):
            price = await self.client.get_index_price("btc_usd")

        self.assertEqual(price, 81700)

    async def test_bad_get_index_price(self):
        session = self.fake_session({"error": "bad request"})
        with patch("app.services.deribit_client.aiohttp.ClientSession", return_value=session):
            with self.assertRaises(KeyError):
                await self.client.get_index_price("btc_usd")


class APITest(unittest.TestCase):
    def setUp(self):
        app.dependency_overrides[get_db] = lambda: MagicMock()
        self.client = TestClient(app)

    def tearDown(self):
        app.dependency_overrides.clear()

    def test_ticker_is_required(self):
        self.assertEqual(self.client.get("/prices/all").status_code, 422)

    def test_all_prices(self):
        data = MagicMock(ticker="btc_usd", current_price=81700, time=1791998066)
        with patch("app.api.prices.PriceRepository") as repository:
            repository.return_value.get_all_by_ticker = AsyncMock(return_value=[data])
            response = self.client.get("/prices/all", params={"ticker": "btc_usd"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()[0]["ticker"], "btc_usd")
        self.assertEqual(response.json()[0]["current_price"], 81700)