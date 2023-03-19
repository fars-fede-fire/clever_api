"""Base entities for Clever API integration."""

from __future__ import annotations

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_USER_ID
from .coordinator import (
    CleverApiSubscriptionUpdateCoordinator,
    CleverApiEvseUpdateCoordinator,
)


class CleverApiSubscriptionEntity(
    CoordinatorEntity[CleverApiSubscriptionUpdateCoordinator]
):
    """Defines a Clever API subscription entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CleverApiSubscriptionUpdateCoordinator) -> None:
        """Initialize Clever API subscription entity."""
        super().__init__(coordinator=coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.data[CONF_USER_ID])},
            manufacturer="Clever",
            name="Clever",
            model="Subscription",
        )


class CleverApiEvseEntity(CoordinatorEntity[CleverApiEvseUpdateCoordinator]):
    """Defines a Clever API EVSE entity."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: CleverApiEvseUpdateCoordinator) -> None:
        """Initialize Clever API EVSE entity."""
        super().__init__(coordinator=coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.config_entry.data[CONF_USER_ID])},
            manufacturer="Clever",
            name="Clever",
            model="Subscription + EVSE",
        )
