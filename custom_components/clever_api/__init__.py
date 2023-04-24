"""Support for Clever EV subscription and EVSE"""

from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    LOGGER,
    CONF_BOX,
    CONF_DEPT_TIME,
    CONF_PHASE_COUNT,
    CONF_DESIRED_RANGE,
    SERVICE_ENABLE_FLEX,
    SERVICE_DISABLE_FLEX,
)

from .coordinator import (
    CleverApiSubscriptionUpdateCoordinator,
    CleverApiEvseUpdateCoordinator,
)
from .clever.clever import Evse

SUB_PLATFORMS = [Platform.SENSOR]
EVSE_PLATFORM = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]

SERVICE_ENABLE_FLEX_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_DEPT_TIME): cv.string,
        vol.Required(CONF_DESIRED_RANGE): cv.positive_int,
        vol.Required(CONF_PHASE_COUNT): cv.positive_int,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup Clever API device from config entry."""

    if entry.data[CONF_BOX] is True:
        evse_coordinator = CleverApiEvseUpdateCoordinator(hass, entry)
        await evse_coordinator.async_config_entry_first_refresh()

        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = evse_coordinator
        await hass.config_entries.async_forward_entry_setups(entry, EVSE_PLATFORM)

        async def enable_flex(call: ServiceCall) -> None:
            """Service to enable flex charging."""
            if (
                evse_coordinator.data.evse_info.data[0].smart_charging_is_enabled
                is not True
            ):
                resp = await evse_coordinator.evse.set_flex(
                    enable=True,
                    effect=call.data[CONF_PHASE_COUNT],
                    dept_time=call.data[CONF_DEPT_TIME],
                    kwh=call.data[CONF_DESIRED_RANGE],
                )
            else:
                await evse_coordinator.evse.set_dept_time(
                    dept_time=call.data[CONF_DEPT_TIME]
                )
                await evse_coordinator.evse.set_kwh(kwh=call.data[CONF_DESIRED_RANGE])

            await evse_coordinator.async_refresh()

        async def disable_flex(call: ServiceCall) -> None:
            """Service to disable flex charging."""
            await evse_coordinator.evse.set_flex(enable=False)
            await evse_coordinator.async_refresh()

        hass.services.async_register(
            DOMAIN, SERVICE_ENABLE_FLEX, enable_flex, schema=SERVICE_ENABLE_FLEX_SCHEMA
        )
        hass.services.async_register(DOMAIN, SERVICE_DISABLE_FLEX, disable_flex)

        return True

    sub_coordinator = CleverApiSubscriptionUpdateCoordinator(hass, entry)
    await sub_coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = sub_coordinator
    await hass.config_entries.async_forward_entry_setups(entry, SUB_PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Clever API config entry."""

    if entry.data[CONF_BOX] is True:
        unload_ok = await hass.config_entries.async_unload_platforms(
            entry, EVSE_PLATFORM
        )
        if unload_ok:
            hass.data[DOMAIN].pop(entry.entry_id)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_ENABLE_FLEX)
            hass.services.async_remove(DOMAIN, SERVICE_DISABLE_FLEX)
            del hass.data[DOMAIN]

    if unload_ok := await hass.config_entries.async_unload_platforms(
        entry, SUB_PLATFORMS
    ):
        del hass.data[DOMAIN][entry.entry_id]
    return unload_ok
