"""DataUpdateCoordinator for Clever API integration."""

from dataclasses import dataclass
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, LOGGER, CONF_BOX_ID, CONF_CONNECTOR_ID, CONF_SUBSCRIPTION_FEE

from .clever.models import ModTransactions, Energitillaeg, EvseState, EvseInfo
from .clever.clever import Evse, Subscription


@dataclass
class CleverApiSubscriptionData:
    """Clever API subscription data stored in DataUpdateCoordinator."""

    transactions: ModTransactions
    energitillaeg: Energitillaeg
    sub_fee: float


class CleverApiSubscriptionUpdateCoordinator(
    DataUpdateCoordinator[CleverApiSubscriptionData]
):
    """Class to manage fetching data for Clever API subscription."""

    config_entry = ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.config_entry = entry
        self.sub = Subscription(
            api_token=entry.data[CONF_API_KEY], session=async_get_clientsession(hass)
        )

        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_subscription",
            update_interval=timedelta(minutes=60),
        )

    async def _async_update_data(self) -> CleverApiSubscriptionData:
        return CleverApiSubscriptionData(
            transactions=await self.sub.get_transactions(),
            energitillaeg=await self.sub.get_energitillaeg(),
            sub_fee=self.config_entry.data[CONF_SUBSCRIPTION_FEE],
        )


@dataclass
class CleverApiEvseData:
    """Clever API EVSE data stored in DataUpdateCoordinator."""

    transactions: ModTransactions
    energitillaeg: Energitillaeg
    sub_fee: float
    evse_state: EvseState
    evse_info: EvseInfo


class CleverApiEvseUpdateCoordinator(DataUpdateCoordinator[CleverApiEvseData]):
    """Class to manage fetching data for Clever API EVSE."""

    config_entry = ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        self.config_entry = entry
        self.sub = Subscription(
            api_token=entry.data[CONF_API_KEY], session=async_get_clientsession(hass)
        )
        self.evse = Evse(
            api_token=entry.data[CONF_API_KEY],
            box_id=entry.data[CONF_BOX_ID],
            connector_id=entry.data[CONF_CONNECTOR_ID],
            session=async_get_clientsession(hass),
        )

        super().__init__(
            hass,
            LOGGER,
            name=f"{DOMAIN}_evse",
            update_interval=timedelta(minutes=1),
        )

    async def _async_update_data(self) -> CleverApiEvseData:
        return CleverApiEvseData(
            evse_state=await self.evse.get_evse_state(),
            evse_info=await self.sub.get_evse_info(),
            transactions=await self.sub.get_transactions(
                box_id=self.config_entry.data[CONF_BOX_ID]
            ),
            energitillaeg=await self.sub.get_energitillaeg(),
            sub_fee=self.config_entry.data[CONF_SUBSCRIPTION_FEE],
        )
