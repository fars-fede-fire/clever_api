"""Clever API sensor platform"""
from datetime import timedelta, datetime

from typing import Callable, Optional

import logging

from homeassistant import core, config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import (
    HomeAssistantType,
    ConfigType,
    DiscoveryInfoType,
)
from homeassistant.const import (
    DEVICE_CLASS_ENERGY,
    ENERGY_KILO_WATT_HOUR,
)

from .clever import Clever, Home

from .const import (
    DOMAIN,
)

SCAN_INTERVAL = timedelta(seconds=60)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: core.HomeAssistant,
    config_entry: config_entries.ConfigEntry,
    async_add_entities,
):
    config = hass.data[DOMAIN][config_entry.entry_id]
    session = async_get_clientsession(hass)
    clever = Clever(session, config["api_key"])
    sensors = [CleverTransactions(clever)]
    if config["chargebox"] == True:
        home = Home(session, config["api_key"], config["charge_box_id"], config["connector_id"])
        sensors.append(CleverHomeChargerEnergy(home))
        _LOGGER.debug(f"charge_box_id: {config['charge_box_id']}, connector_id: {config['connector_id']}")
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
    if config["chargebox"] == True:
        home = Home(session, config["api_key"], config["charge_box_id"], config["connector_id"])
        sensors.append(CleverHomeChargerEnergy(home))
    async_add_entities(sensors, update_before_add=True)


class CleverHomeChargerEnergy(Entity):
    """Representation of Clever current charging session """

    device_class = DEVICE_CLASS_ENERGY
    _attr_unit_of_measurement = ENERGY_KILO_WATT_HOUR

    def __init__(self, home: Home):
        super().__init__()
        self.home = home
        self._site_data = None
        self._attr_name = "Clever current session consumption"
        self._state = None
        self._available = True
        self._last_upd = None

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        """Return other details about the sensor state."""
        attrs = {}
        attrs["last_updated_server_timestamp"] = self._last_upd
        return attrs

    async def async_update(self):
        data = await self.home.get_charger_state()
        self._last_upd = data["timestamp"]
        _LOGGER.debug(f"{data}")
        if data["data"]["consumedWh"] is not "Unknown":
            self._state = round(float(data["data"]["consumedWh"]/1_000), 2)
        else:
            self._state = 0



class CleverTransactions(Entity):
    """Representation of Clever Transactions sensor."""

    device_class = DEVICE_CLASS_ENERGY
    _attr_unit_of_measurement = ENERGY_KILO_WATT_HOUR

    def __init__(self, clever: Clever):
        super().__init__()
        self.clever = clever
        self.attrs = {}
        self._attr_name = "Clever consumption this month"
        self._state = None
        self._available = True
        self._last_upd = None

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        """Return other details about the sensor state."""
        attrs = {}
        attrs["last_updated_server_timestamp"] = self._last_upd
        return attrs

    async def async_update(self):
        transaction_data = await self.clever.get_transactions()
        self._last_upd = transaction_data["timestamp"]
        today = datetime.today()
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_of_month_in_ms = start_of_month.timestamp() * 1_000_000
        kwh_this_month = 0
        _LOGGER.debug(f"{transaction_data}")
        for item in transaction_data["data"]["consumptionRecords"]:
            if item["startTimeUtc"] >= start_of_month_in_ms:
                kwh_this_month += item["kWh"]

        self._state = round(kwh_this_month, 2)
