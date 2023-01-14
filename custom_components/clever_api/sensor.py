"""Clever API sensor platform"""
from datetime import timedelta, datetime

from typing import Callable, Optional

from homeassistant import core, config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    HomeAssistantType,
    ConfigType,
    DiscoveryInfoType,
)

from .clever import Clever

from .const import (
    DOMAIN,
)

SCAN_INTERVAL = timedelta(hours=4)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    config = hass.data[DOMAIN][config_entry.entry_id]
    session = async_get_clientsession(hass)
    clever = Clever(session, config["api_key"])
    sensors = [CleverTransactions(clever)]
    async_add_entities(sensors, update_before_add=True)


async def async_setup_platform(
    hass: HomeAssistantType,
    config: ConfigType,
    async_add_entities: Callable,
    discovery_info: Optional[DiscoveryInfoType] = None,
):
    session = async_get_clientsession(hass)
    clever = Clever(session, config["api_key"])
    sensors = [CleverTransactions(clever)]
    async_add_entities(sensors, update_before_add=True)


class CleverTransactions(Entity):
    """Representation of Clever Transactions sensor."""

    def __init__(self, clever: Clever):
        super().__init__()
        self.clever = clever
        self.attrs = {}
        self._attr_name = "Clever consumption this month"
        self._state = None
        self._available = True

    @property
    def state(self):
        return self._state

    async def async_update(self):
        transaction_data = await self.clever.get_transactions()
        today = datetime.today()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_month_in_ms = start_of_month.timestamp() * 1_000_000
        kwh_this_month = 0
        for item in transaction_data["data"]["consumptionRecords"]:
            if item["startTimeUtc"] >= start_of_month_in_ms:
                kwh_this_month += item["kWh"]

        self._state = kwh_this_month
