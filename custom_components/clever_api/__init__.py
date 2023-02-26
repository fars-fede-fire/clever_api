"""Support for Clever EV subscription and EVSE"""

from __future__ import annotations

from dataclasses import dataclass, field

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN

# from .device import CleverApiDevice


@dataclass
class CleverApiData:
    """Class for sharing data within Clever API integration."""

    devices: dict = field(default_factory=dict)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Setup Clever API integration."""
    hass.data[DOMAIN] = CleverApiData()
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup Clever API device from config entry."""

    device = CleverApiDevice(hass, entry)

    return await device.async_setup()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Clever API config entry."""

    data = hass.data[DOMAIN]

    device = data.devices.pop(entry.entry_id)
    result = await device.async_unload()

    return result
