"""Support for Clever API sensors."""

from __future__ import annotations

from asyncio import sleep
from collections.abc import Callable, Awaitable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import (
    SwitchEntity,
    SwitchEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import (
    CleverApiEvseData,
    CleverApiEvseUpdateCoordinator,
)
from .clever.clever import Evse
from .entity import CleverApiEvseEntity


@dataclass
class CleverApiSwitchEvseEntityMixin:
    """Mixin values for Clever API EVSE entities."""

    is_on_fn: Callable[[CleverApiEvseData], bool | None]
    set_fn: Callable[[Evse, bool], Awaitable[Any]]


@dataclass
class CleverApiSwitchEvseEntityDescription(
    SwitchEntityDescription, CleverApiSwitchEvseEntityMixin
):
    """Class describing Clever API EVSE switch sensor entities."""


SWITCHES = [
    CleverApiSwitchEvseEntityDescription(
        key="preheat",
        name="Preheat",
        icon="mdi:radiator",
        is_on_fn=lambda x: False
        if x.evse_info.data[0].smart_charging_is_enabled is False
        else x.evse_info.data[
            0
        ].smart_charging_configuration.user_configuration.preheat_in_minutes
        == 30,
        set_fn=lambda client, enable: client.set_climate(enable=enable),
    ),
    CleverApiSwitchEvseEntityDescription(
        key="skip_io",
        name="Skip Intelligent Opladning",
        icon="mdi:fast-forward",
        is_on_fn=lambda x: False
        if x.evse_info.data[0].smart_charging_is_enabled is False
        or x.evse_state.data is None
        else x.evse_state.data.charging_plan.boost_status.is_boosted,
        set_fn=lambda client, enable: client.set_unlimited_boost(enable=enable),
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup Clever API switch from config entry."""
    evse_coordinator: CleverApiEvseUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        CleverApiEvseSwitchEntity(
            coordinator=evse_coordinator,
            description=description,
        )
        for description in SWITCHES
    )


class CleverApiEvseSwitchEntity(CleverApiEvseEntity, SwitchEntity):
    """Representation of a Clever EVSE API switch sensor."""

    entity_description: CleverApiSwitchEvseEntityDescription

    def __init__(
        self,
        coordinator: CleverApiEvseUpdateCoordinator,
        description: CleverApiSwitchEvseEntityDescription,
    ) -> None:
        """Initiate Clever API switch"""
        super().__init__(coordinator)

        self.entity_description = description
        self._attr_unique_id = f"{description.key}"

    @property
    def is_on(self) -> bool:
        """Return switch sensor value."""
        return self.entity_description.is_on_fn(self.coordinator.data)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn entity on"""
        await self.entity_description.set_fn(self.coordinator.evse, True)
        await sleep(2)
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn entity off"""
        await self.entity_description.set_fn(self.coordinator.evse, False)
        await sleep(2)
        await self.coordinator.async_refresh()
