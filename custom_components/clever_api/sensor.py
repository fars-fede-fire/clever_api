"""Support for Clever API sensors."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER, CONF_BOX, CONF_USER_ID
from .coordinator import (
    CleverApiSubscriptionUpdateCoordinator,
    CleverApiSubscriptionData,
    CleverApiEvseData,
    CleverApiEvseUpdateCoordinator,
)
from .entity import CleverApiSubscriptionEntity, CleverApiEvseEntity


@dataclass
class CleverApiSubscriptionEntityMixin:
    """Mixin values for Clever API subscription entities."""

    value_fn: Callable[[CleverApiSubscriptionData], float]
    attr_name: str | None
    attr_fn: Callable[[CleverApiSubscriptionData], float | None]


@dataclass
class CleverApiEvseEntityMixin:
    """Mixin values for Clever API EVSE entities."""

    value_fn: Callable[[CleverApiEvseData], float]
    attr_name: str | None
    attr_fn: Callable[[CleverApiEvseData], float | None]


@dataclass
class CleverApiSubscriptionEntityDescription(
    SensorEntityDescription, CleverApiSubscriptionEntityMixin
):
    """Class describing Clever API subscription sensor entities"""


@dataclass
class CleverApiEvseEntityDescription(SensorEntityDescription, CleverApiEvseEntityMixin):
    """Class describing Clever API EVSE sensor entities"""


SUBSCRIPTION_SENSORS = [
    CleverApiSubscriptionEntityDescription(
        key="kwh_this_month",
        name="Energy this month",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda x: x.transactions.kwh_this_month,
        attr_fn=lambda x: x.transactions.last_charge,
        attr_name="last_update",
    ),
    CleverApiSubscriptionEntityDescription(
        key="energi_tillaeg",
        name="Energitillaeg",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="DKK/kWh",
        value_fn=lambda x: x.energitillaeg.data.energy_surcharge_price_dkk,
        attr_fn=lambda x: x.energitillaeg.data.end_date,
        attr_name="last_updated",
    ),
    CleverApiSubscriptionEntityDescription(
        key="estimated_price",
        name="Estimated total price this month",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="DKK",
        value_fn=lambda x: (
            x.transactions.kwh_this_month
            * x.energitillaeg.data.energy_surcharge_price_dkk
        )
        + x.sub_fee,
        attr_fn=lambda x: (
            x.transactions.kwh_this_month
            * x.energitillaeg.data.energy_surcharge_price_dkk
        ),
        attr_name="energitillaeg",
    ),
]

EVSE_SENSORS = [
    CleverApiEvseEntityDescription(
        key="kwh_this_month",
        name="Energy this month",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda x: x.transactions.kwh_this_month,
        attr_fn=lambda x: x.transactions.last_charge,
        attr_name="last_update",
    ),
    CleverApiEvseEntityDescription(
        key="kwh_this_month_box",
        name="Energy this month on box",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda x: x.transactions.kwh_this_month_box,
        attr_fn=None,
        attr_name=None,
    ),
    CleverApiEvseEntityDescription(
        key="energi_tillaeg",
        name="Energitillaeg",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="DKK/kWh",
        value_fn=lambda x: x.energitillaeg.data.energy_surcharge_price_dkk,
        attr_fn=lambda x: x.energitillaeg.data.end_date,
        attr_name="last_updated",
    ),
    CleverApiEvseEntityDescription(
        key="estimated_price",
        name="Estimated total price this month",
        device_class=SensorDeviceClass.MONETARY,
        native_unit_of_measurement="DKK",
        value_fn=lambda x: (
            x.transactions.kwh_this_month
            * x.energitillaeg.data.energy_surcharge_price_dkk
        )
        + x.sub_fee,
        attr_fn=lambda x: (
            x.transactions.kwh_this_month
            * x.energitillaeg.data.energy_surcharge_price_dkk
        ),
        attr_name="energitillaeg",
    ),
    CleverApiEvseEntityDescription(
        key="evse_energy",
        name="Energy this charging session",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value_fn=lambda x: x.evse_state.data.consumed_wh
        if hasattr(x.evse_state.data, "consumed_wh")
        else 0,
        attr_name=None,
        attr_fn=None,
    ),
    CleverApiEvseEntityDescription(
        key="evse_state",
        name="State of charger",
        device_class=SensorDeviceClass.ENUM,
        value_fn=lambda x: x.evse_state.data.status
        if hasattr(x.evse_state.data, "status")
        else "Unplugged",
        attr_name=None,
        attr_fn=None,
    ),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup Clever API sensors from config entry."""

    if entry.data[CONF_BOX] is True:
        evse_coordinator: CleverApiEvseUpdateCoordinator = hass.data[DOMAIN][
            entry.entry_id
        ]

        async_add_entities(
            CleverApiEvseSensorEntity(
                coordinator=evse_coordinator,
                description=description,
            )
            for description in EVSE_SENSORS
        )

    else:
        sub_coordinator: CleverApiSubscriptionUpdateCoordinator = hass.data[DOMAIN][
            entry.entry_id
        ]
        async_add_entities(
            CleverApiSubscriptionSensorEntity(
                coordinator=sub_coordinator,
                description=description,
            )
            for description in SUBSCRIPTION_SENSORS
        )


class CleverApiSubscriptionSensorEntity(CleverApiSubscriptionEntity, SensorEntity):
    """Representation of a Clever Subscription API sensor."""

    entity_description: CleverApiSubscriptionEntityDescription

    def __init__(
        self,
        coordinator: CleverApiSubscriptionUpdateCoordinator,
        description: CleverApiSubscriptionEntityDescription,
    ) -> None:
        """Initiate Clever API sensor"""
        super().__init__(coordinator)

        self.entity_description = description
        self._attr_unique_id = f"{description.key}"

    @property
    def native_value(self) -> float:
        """Return sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self):
        if self.entity_description.attr_name is not None:
            return {
                self.entity_description.attr_name: self.entity_description.attr_fn(
                    self.coordinator.data
                )
            }
        return None


class CleverApiEvseSensorEntity(CleverApiEvseEntity, SensorEntity):
    """Representation of a Clever Subscription API sensor."""

    entity_description: CleverApiEvseEntityDescription

    def __init__(
        self,
        coordinator: CleverApiEvseUpdateCoordinator,
        description: CleverApiEvseEntityDescription,
    ) -> None:
        """Initiate Clever API sensor"""
        super().__init__(coordinator)

        self.entity_description = description
        self._attr_unique_id = (
            f"{self.coordinator.config_entry.data[CONF_USER_ID]}_{description.key}"
        )

    @property
    def native_value(self) -> float:
        """Return sensor value."""
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self):
        if self.entity_description.attr_name is not None:
            return {
                self.entity_description.attr_name: self.entity_description.attr_fn(
                    self.coordinator.data
                )
            }
        return None
