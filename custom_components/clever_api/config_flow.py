"""Config flow for Clever API"""

from __future__ import annotations

from urllib.parse import unquote

from typing import Any, Dict
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_API_KEY, CONF_API_TOKEN
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get,
)

from .const import (
    DOMAIN,
    LOGGER,
    CONF_URL,
    CONF_BOX,
    CONF_USER_ID,
    CONF_BOX_ID,
    CONF_CONNECTOR_ID,
    CONF_SUBSCRIPTION_FEE,
)

from .clever.clever import Auth, Subscription

REAUTH = "reauth"

EMAIL_SCHEMA = vol.Schema({vol.Required(CONF_EMAIL): str})
URL_SCHEMA = vol.Schema({vol.Required(CONF_URL): str})
BOX_SCHEMA = vol.Schema({vol.Required(CONF_BOX): bool})
MISC_SCHEMA = vol.Schema({vol.Optional(CONF_SUBSCRIPTION_FEE, default=799): int})
REAUTH_SCHEMA = vol.Schema({vol.Required(REAUTH): bool})


class CleverApiConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle Clever API config flow"""

    VERSION = 1

    email: str
    url: str
    api_token: str
    api_key: str
    first_name: str
    last_name: str
    secret_code: str
    user_secret: str
    customer_id: str
    add_box: bool
    box_charge_id: int = None
    box_connector_id: int = None
    subscription_fee: float = None

    def __init__(self) -> None:
        """Initialize Clever API flow"""
        self.device = None

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Define a Clever API device for config flow"""

        errors = {}

        if user_input is not None:
            self.email = user_input[CONF_EMAIL]
            session = async_get_clientsession(self.hass)

            await Auth(session=session).send_auth_email(self.email)

            return await self.async_step_url()

        return self.async_show_form(
            step_id="user", data_schema=EMAIL_SCHEMA, errors=errors
        )

    async def async_step_url(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Insert URL and setup integration."""

        errors = {}

        if user_input is not None:
            self.url = user_input[CONF_URL]
            self.url = unquote(self.url)
            # A bit hacky, but this does the trick.
            # The url contains 2 urls. We only need the second
            # url for this step.
            self.url = self.url.partition("https") # Search for first https and cut everything in front off.
            self.url = self.url[2].partition("https") # Search for https again in the new string.
            self.url = self.url[1] + self.url[2] # partition split the string up in 3 parts. We need the first (https) and the second.
            session = async_get_clientsession(self.hass)

            auth = Auth(session=session)

            resp = await auth.verify_link(auth_link=self.url, email=self.email)

            self.first_name = resp.data["firstName"]
            self.last_name = resp.data["lastName"]
            self.secret_code = resp.secret_code

            resp = await auth.obtain_user_secret(
                email=self.email,
                first_name=self.first_name,
                last_name=self.last_name,
                secret_code=self.secret_code,
            )
            self.api_token = resp.data["userSecret"]

            resp = await auth.obtain_api_token(
                user_secret=self.api_token, email=self.email
            )

            self.api_key = resp.data

            sub = Subscription(session=session, api_token=self.api_key)

            user_data = await sub.get_user_info()

            self.customer_id = user_data.data.customer_id

            await self.async_set_unique_id(self.customer_id)

            return await self.async_step_box()

        return self.async_show_form(
            step_id="url", data_schema=URL_SCHEMA, errors=errors
        )

    async def async_step_box(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Setup Clever EVSE"""

        errors = {}

        if user_input is not None:
            self.add_box = user_input[CONF_BOX]
            if self.add_box is True:
                session = async_get_clientsession(self.hass)
                sub = Subscription(session=session, api_token=self.api_key)
                resp = await sub.get_evse_info()

                self.box_charge_id = resp.data[0].charge_box_id
                self.box_connector_id = resp.data[0].connector_id

            return await self.async_step_misc()

        return self.async_show_form(
            step_id="box", data_schema=BOX_SCHEMA, errors=errors
        )

    async def async_step_misc(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle extra steps in setup"""

        errors = {}

        if user_input is not None:
            self.subscription_fee = user_input[CONF_SUBSCRIPTION_FEE]

            data = {
                CONF_API_KEY: self.api_key,
                CONF_API_TOKEN: self.api_token,
                CONF_EMAIL: self.email,
                CONF_USER_ID: self.customer_id,
                CONF_BOX: self.add_box,
                CONF_BOX_ID: self.box_charge_id,
                CONF_CONNECTOR_ID: self.box_connector_id,
                CONF_SUBSCRIPTION_FEE: self.subscription_fee,
            }

            return self.async_create_entry(title=self.email, data=data)

        return self.async_show_form(
            step_id="misc", data_schema=MISC_SCHEMA, errors=errors
        )


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for the component."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry
        self.options = config_entry.options

    async def async_step_init(self, user_input: None = None) -> FlowResult:
        """Manage options."""
        return await self.async_step_reauth()

    async def async_step_reauth(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage reauth."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if user_input[REAUTH] is True:
                current_config = self.config_entry.data

                session = async_get_clientsession(self.hass)

                auth = Auth(session=session)

                resp = await auth.obtain_api_token(
                    user_secret=current_config[CONF_API_TOKEN],
                    email=current_config[CONF_EMAIL],
                )
                LOGGER.debug(current_config[CONF_API_KEY])
                new_config = current_config.copy()
                new_config[CONF_API_KEY] = resp.data

                self.hass.config_entries.async_update_entry(
                    self.config_entry, data=new_config
                )
                return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="reauth", data_schema=REAUTH_SCHEMA, errors=errors
        )
