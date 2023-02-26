"""Asynchronous Python client for Clever EV charger subscription and EV charger at home"""
from __future__ import annotations

import asyncio

from dataclasses import dataclass
from datetime import datetime
from typing import Any, cast

import async_timeout
from aiohttp.client import ClientSession
from aiohttp.hdrs import METH_GET, METH_POST
from yarl import URL

from .exceptions import (
    CleverError,
    CleverConnectionError,
)
from .models import (
    SendEmail,
    VerifyLink,
    ObtainUserSecret,
    ObtainApiToken,
    UserInfo,
    Transactions,
    EvseInfo,
    EvseState,
    Energitillaeg,
)


@dataclass
class Clever:
    """Class for handling connection with Clever backend"""

    request_timeout: int = 10
    session: ClientSession | None = None
    _close_session: bool = False

    async def _request(
        self,
        url: str,
        method: str = METH_GET,
        data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Handle request to Clever backend"""

        headers = {"authorization": "Basic bW9iaWxlYXBwOmFwaWtleQ=="}

        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        try:
            async with async_timeout.timeout(self.request_timeout):
                response = await self.session.request(
                    method,
                    url,
                    json=data,
                    headers=headers,
                )
                response.raise_for_status()
        except asyncio.TimeoutError as exception:
            msg = "Timeout while connecting to Clever backend"
            raise CleverConnectionError(msg) from exception

        return cast(dict[str, Any], await response.json())

    async def close(self) -> None:
        """Close client session."""

        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> Clever:
        """Async enter."""

        return self

    async def __aexit__(self, *_exc_inf: Any) -> None:
        """Async exit."""

        await self.close()


class Auth(Clever):
    """Handles Clever API auth process"""

    async def send_auth_email(self, email: str) -> SendEmail:
        """Request a verify login email from Clever"""
        url = f"https://mobileapp-backend.clever.dk/api/mobile/customer/verifyEmail?email={email}"
        resp = await self._request(url)
        return SendEmail.parse_obj(resp)

    async def verify_link(self, auth_link: str, email: str) -> VerifyLink:
        """Obtain secretCode send to email."""
        secret_code = URL(auth_link).query["secretCode"]
        url = f"https://mobileapp-backend.clever.dk/api/mobile/customer/verifySignupToken?token={secret_code}&email={email}"

        resp = await self._request(url)
        resp["secret_code"] = secret_code
        model = VerifyLink.parse_obj(resp)
        if model.data["result"] != "Verified":
            msg = model.data["result"]
            raise CleverError(msg)
        return model

    async def obtain_user_secret(
        self, email: str, first_name: str, last_name: str, secret_code: str
    ) -> ObtainUserSecret:
        """Exchange secret_code for user_secret."""

        url = f"https://mobileapp-backend.clever.dk/api//v2/customer/registerProfile"
        payload = {
            "email": email,
            "firstName": first_name,
            "lastName": last_name,
            "token": secret_code,
        }
        resp = await self._request(url, method=METH_POST, data=payload)
        model = ObtainUserSecret.parse_obj(resp)
        if model.data["userSecret"] == "null":
            msg = model.data["verificationResponse"]["result"]
            raise CleverError(msg)
        return model

    async def obtain_api_token(self, user_secret: str, email: str):
        """Exchange user_secret for api_token."""

        url = f"https://mobileapp-backend.clever.dk/api/mobile/customer/loginWithSecretCode?secret={user_secret}&email={email}"
        resp = await self._request(url)
        model = ObtainApiToken.parse_obj(resp)
        if model.data is None:
            msg = model.statusMessage
            raise CleverError(msg)
        return model


@dataclass
class Subscription(Clever):
    """Dataclass representing a Clever subscription."""

    api_token: str = None

    async def get_user_info(self) -> UserInfo:
        """Get info of user"""

        url = f"https://mobileapp-backend.clever.dk/api//v2/customer/{self.api_token}/getProfile?"
        resp = await self._request(url)
        model = UserInfo.parse_obj(resp)
        return model

    async def get_transactions(self) -> Transactions:
        """Get charging transactions"""
        url = f"https://mobileapp-backend.clever.dk/api//v2/consumption/{self.api_token}/history"
        resp = await self._request(url)
        model = Transactions.parse_obj(resp)
        return model

    async def get_evse_info(self) -> EvseInfo:
        """Get info about EVSE"""
        url = f"https://mobileapp-backend.clever.dk/api//v3/{self.api_token}/installations?"
        resp = await self._request(url)
        model = EvseInfo.parse_obj(resp)
        return model


@dataclass
class Evse(Clever):
    """Dataclass for communication with home charge box."""

    api_token: str = None
    box_id: int = None
    connector_id: int = None

    async def get_evse_state(self) -> EvseState:
        """Get state of EVSE"""
        url = f"https://mobileapp-backend.clever.dk/api//v4/transactions/{self.api_token}/{self.box_id}/connector/{self.connector_id}?chargepointId={self.box_id}&connector={self.connector_id}"
        resp = await self._request(url)
        model = EvseState.parse_obj(resp)
        return model

    async def set_flex(
        self, enable: bool, effect: int = None, dept_time: str = None, kwh: int = None
    ) -> None:
        """Enable or disable flex charging"""
        if enable is True:
            url = f"https://mobileapp-backend.clever.dk/api//v3/flex/{self.api_token}/chargepoints/{self.box_id}/connectors/{self.connector_id}/migrate?"
            data = {
                "configuredEffect": {"phaseCount": effect},
                "departureTime": {"time": dept_time},
                "desiredRange": {"range": kwh},
            }

            await self._request(url, method=METH_POST, data=data)
        else:
            url = f"https://mobileapp-backend.clever.dk/api//v3/flex/{self.api_token}/chargepoints/{self.box_id}/connectors/{self.connector_id}/enable?"
            data = {"enable": False}

            await self._request(url, method=METH_POST, data=data)

    async def set_climate(self, enable: bool = None) -> None:
        """Set climate start"""
        if enable is True:
            url = f"https://mobileapp-backend.clever.dk/api//v4/smartcharging/{self.api_token}/chargePoints/{self.box_id}/connectors/{self.connector_id}/settings/preheat?enable=true"
            await self._request(url, method=METH_POST)
        else:
            url = f"https://mobileapp-backend.clever.dk/api//v4/smartcharging/{self.api_token}/chargePoints/{self.box_id}/connectors/{self.connector_id}/settings/preheat?enable=false"
            await self._request(url, method=METH_POST)

    async def set_unlimited_boost(self) -> None:
        """Skip smart charging for this session"""
        url = f"https://mobileapp-backend.clever.dk/api//v4/smartcharging/{self.api_token}/chargePoints/{self.box_id}/connectors/{self.connector_id}/boost?"
        await self._request(url, method=METH_POST)

    async def set_timed_boost(self) -> None:
        """Skip smart charging for 30 minutes"""
        url = f"https://mobileapp-backend.clever.dk/api//v4/smartcharging/{self.api_token}/chargePoints/{self.box_id}/connectors/{self.connector_id}/timebox-boost?"
        await self._request(url, method=METH_POST)

    async def disable_boost(self) -> None:
        """Return to smart charging."""
        url = f"https://mobileapp-backend.clever.dk/api//v4/smartcharging/{self.api_token}/chargePoints/{self.box_id}/connectors/{self.connector_id}/unboost?"
        await self._request(url, method=METH_POST)

    async def set_kwh(self, kwh: int = None) -> None:
        """Set kWh need for smart charging"""
        url = f"https://mobileapp-backend.clever.dk/api//v3/flex/{self.api_token}/chargepoints/{self.box_id}/connectors/{self.connector_id}/range"
        data = {"range": kwh}
        await self._request(url, method=METH_POST, data=data)

    async def set_dept_time(self, dept_time: str = None) -> None:
        """Set depature time for smart charging in format HH:MM"""
        url = f"https://mobileapp-backend.clever.dk/api//v3/flex/{self.api_token}/chargepoints/{self.box_id}/connectors/{self.connector_id}/schedule"
        data = {"time": dept_time}
        await self._request(url, method=METH_POST, data=data)


class Util(Clever):
    """Get data without authentication."""

    async def get_energitillaeg(self) -> Energitillaeg:
        """Calculate Energitillæg from spot prices"""
        url = str(
            "https://api.energidataservice.dk/dataset/Elspotprices?offset=0&start=StartOfMonth&end=StartOfMonth+P1M&filter=%7B%22PriceArea%22:[%22DK1%22,%22DK2%22]%7D&sort=HourDK%20DESC&timezone=dk"
        )
        resp = await self._request(url)
        spotprice_sum = 0
        for price in resp["records"]:
            spotprice_sum += price["SpotPriceDKK"]

        last_day_included = (
            datetime.fromisoformat(resp["records"][0]["HourDK"])
        ).date()

        spotprice_total = resp["total"]
        # Divide by 1_000 to get in kr/kWh
        raw_energitillaeg = (spotprice_sum / spotprice_total) / 1_000

        model = Energitillaeg.parse_obj(
            {
                "raw_energitillaeg": raw_energitillaeg,
                "last_day_included": last_day_included,
            }
        )
        return model
