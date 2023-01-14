from datetime import datetime
from aiohttp import ClientSession, ClientResponse


class Clever:
    """Make API calls to Clever"""

    def __init__(self, websession: ClientSession, api_key) -> None:
        self.websession = websession
        self.api_key = api_key
        self.headers = {"authorization": "Basic bW9iaWxlYXBwOmFwaWtleQ=="}

    async def get_transactions(self) -> ClientResponse:
        """Get charching history"""
        now = datetime.now()
        date_time = now.strftime("%Y-%m-%dT%H:%M:%S")
        resp = await self.websession.request(
            "get",
            f"https://mobileapp-backend.clever.dk/api//v2/consumption/{self.api_key}/history?lastUpdatedAt={date_time}.127%2B0100",
            headers=self.headers,
        )

        return await resp.json()


class Home:
    """API calls to Clever charger at home"""

    def __init__(self, websession: ClientSession, api_key, charge_box_id, connector):
        self.websession = websession
        self.api_key = api_key
        self.charge_box_id = charge_box_id
        self.connector = connector
        self.headers = {"authorization": "Basic bW9iaWxlYXBwOmFwaWtleQ=="}

    async def get_charger_state(self) -> ClientResponse:
        """Get current state of home charger"""
        return await self.websession.request(
            "get",
            f"https://mobileapp-backend.clever.dk/api//v4/transactions/{self.api_key}/{self.charge_box_id}/connector/{self.connector}?chargepointId={self.charge_box_id}&connector={self.connector}",
            headers=self.headers,
        )

    async def enable_climate_start(self):
        """Enable climate start"""
        return await self.websession.request(
            "post",
            f"https://mobileapp-backend.clever.dk/api//v4/smartcharging/{self.api_key}/chargePoints/{self.charge_box_id}/connectors/{self.connector}/settings/preheat?enable=true",
            headers=self.headers,
        )
