"""Support for Clever API sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Dict

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .coordinator import (
    CleverApiEvseData,
    CleverApiEvseUpdateCoordinator,
)
from .entity import CleverApiEvseEntity


@dataclass
class CleverApiBinarySensorEvseEntityMixin:
    """Mixin values for Clever API EVSE entities."""

    value_fn: Callable[[CleverApiEvseData], Any]
    attrs: Dict[str, Callable[[CleverApiEvseData], Any]]


@dataclass
class CleverApiBinarySensorEvseEntityDescription(
    BinarySensorEntityDescription, CleverApiBinarySensorEvseEntityMixin
):
    """Class describing Clever API EVSE binary sensor entities."""


BINARY_SENSORS = [
    CleverApiBinarySensorEvseEntityDescription(
        key="IO",
        name="Intelligent Opladning",
        icon="mdi:radiobox-blank",
        value_fn=lambda x: x.evse_info.data[0].smart_charging_is_enabled,
        attrs={
            "planned_depature": lambda x: None
            if x.evse_info.data[0].smart_charging_is_enabled is False
            else x.evse_info.data[
                0
            ].smart_charging_configuration.user_configuration.departure_time["time"],
            "desired_range": lambda x: None
            if x.evse_info.data[0].smart_charging_is_enabled is False
            else x.evse_info.data[
                0
            ].smart_charging_configuration.user_configuration.desired_range[
                "desiredRange"
            ],
            "configured_effect": lambda x: None
            if x.evse_info.data[0].smart_charging_is_enabled is False
            else x.evse_info.data[
                0
            ].smart_charging_configuration.user_configuration.configured_effect[
                "phaseCount"
            ],
            "preheat_enabled": lambda x: None
            if x.evse_info.data[0].smart_charging_is_enabled is False
            else x.evse_info.data[
                0
            ].smart_charging_configuration.user_configuration.preheat_in_minutes
            == 30,
        },
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup Clever API binary sensors from config entry."""
    evse_coordinator: CleverApiEvseUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        CleverApiEvseBinarySensorEntity(
            coordinator=evse_coordinator,
            description=description,
        )
        for description in BINARY_SENSORS
    )


class CleverApiEvseBinarySensorEntity(CleverApiEvseEntity, BinarySensorEntity):
    """Representation of a Clever EVSE API binary sensor."""

    entity_description: CleverApiBinarySensorEvseEntityDescription

    def __init__(
        self,
        coordinator: CleverApiEvseUpdateCoordinator,
        description: CleverApiBinarySensorEvseEntityDescription,
    ) -> None:
        """Initiate Clever API binary sensor"""
        super().__init__(coordinator)

        self.entity_description = description
        self._attr_unique_id = f"{description.key}"

    @property
    def is_on(self) -> bool:
        """Return binary sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self):
        attr = {}
        for key in self.entity_description.attrs:
            attr[key] = self.entity_description.attrs[key](self.coordinator.data)

        return attr
