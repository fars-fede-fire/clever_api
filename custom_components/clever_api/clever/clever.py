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
    ModTransactions,
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
        
        resp = await self._request(url)
        return SendEmail.parse_obj(resp)

    async def verify_link(self, auth_link: str, email: str) -> VerifyLink:
        """Obtain secretCode send to email."""
        secret_code = URL(auth_link).query["secretCode"]
        url = "censored"

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

        url = "censored"
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

        url = "censored"
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

        url = "censored"
        resp = await self._request(url)
        model = UserInfo.parse_obj(resp)
        return model

    async def get_transactions(self, box_id=None) -> Transactions:
        """Get charging transactions"""
        url = "censored"
        resp = await self._request(url)
        model = Transactions.parse_obj(resp)
        today = datetime.today()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_month_in_ms = start_of_month.timestamp() * 1_000_000
        kwh_this_month = 0
        for item in model.data.consumption_records:
            if item.start_time_utc >= start_of_month_in_ms:
                kwh_this_month += item.k_wh
        last_registered_transaction = datetime.fromtimestamp(
            (model.data.consumption_records[-1].stop_time_local) / 1_000_000
        )

        if box_id is not None:
            kwh_this_month_box = 0
            for item in model.data.consumption_records:
                if item.start_time_utc >= start_of_month_in_ms:
                    if item.charge_point_id == box_id:
                        kwh_this_month_box += item.k_wh

            return_model = ModTransactions.parse_obj(
                {
                    "kwh_this_month": kwh_this_month,
                    "kwh_this_month_box": kwh_this_month_box,
                    "last_charge": last_registered_transaction,
                }
            )

            return return_model

        return_model = ModTransactions.parse_obj(
            {
                "kwh_this_month": kwh_this_month,
                "kwh_this_month_box": None,
                "last_charge": last_registered_transaction,
            }
        )

        return return_model

    async def get_evse_info(self) -> EvseInfo:
        """Get info about EVSE"""
        url = "censored"
        resp = await self._request(url)
        model = EvseInfo.parse_obj(resp)
        return model

    async def get_energitillaeg(self) -> Energitillaeg:
        """Get energitillaeg."""
        url = "censored"
        resp = await self._request(url)
        model = Energitillaeg.parse_obj(resp)
        return model


@dataclass
class Evse(Clever):
    """Dataclass for communication with home charge box."""

    api_token: str = None
    box_id: int = None
    connector_id: int = None

    async def get_evse_state(self) -> EvseState:
        """Get state of EVSE"""
        url = "censored"
        resp = await self._request(url)
        model = EvseState.parse_obj(resp)
        return model

    async def set_flex(
        self, enable: bool, effect: int = None, dept_time: str = None, kwh: int = None
    ) -> None:
        """Enable or disable flex charging"""
        if enable is True:
            url = "censored"
            data = {
                "configuredEffect": {"phaseCount": effect},
                "departureTime": {"time": dept_time},
                "desiredRange": {"range": kwh},
            }

            resp = await self._request(url, method=METH_POST, data=data)

            return resp
        else:
            url = "censored"
            data = {"enable": False}

            await self._request(url, method=METH_POST, data=data)

    async def set_climate(self, enable: bool = None) -> None:
        """Set climate start"""
        if enable is True:
            url = "censored"
            await self._request(url, method=METH_POST)
        else:
            url = "censored"
            await self._request(url, method=METH_POST)

    async def set_unlimited_boost(self, enable: bool = None) -> None:
        """Skip smart charging for this session"""
        if enable is True:
            url = "censored"
            await self._request(url, method=METH_POST)
        else:
            await self.disable_boost()

    async def set_timed_boost(self) -> None:
        """Skip smart charging for 30 minutes"""
        url = "censored"
        await self._request(url, method=METH_POST)

    async def disable_boost(self) -> None:
        """Return to smart charging."""
        url = "censored"
        await self._request(url, method=METH_POST)

    async def set_kwh(self, kwh: int = None) -> None:
        """Set kWh need for smart charging"""
        url = "censored"
        data = {"range": kwh}
        await self._request(url, method=METH_POST, data=data)

    async def set_dept_time(self, dept_time: str = None) -> None:
        """Set depature time for smart charging in format HH:MM"""
        url = "censored"
        data = {"time": dept_time}
        await self._request(url, method=METH_POST, data=data)
