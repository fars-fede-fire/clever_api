"""Config flow for Clever API"""

from typing import Any
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_API_KEY, CONF_API_TOKEN
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, LOGGER, CONF_URL
from .clever.clever import Util, Auth, Subscription, Evse

EMAIL_SCHEMA = vol.Schema({vol.Required(CONF_EMAIL): str})
URL_SCHEMA = vol.Schema({vol.Required(CONF_URL): str})


class CleverApiFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
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

    def __init__(self) -> None:
        """Initialize Clever API flow"""
        self.device = None

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
            session = async_get_clientsession(self.hass)

            auth = Auth(session=session)

            resp = await auth.verify_link(auth_link=self.url, email=self.email)

            LOGGER.debug(resp)
            self.first_name = resp.data["firstName"]
            self.last_name = resp.data["lastName"]
            self.secret_code = resp.secret_code

            resp = await auth.obtain_user_secret(
                email=self.email,
                first_name=self.first_name,
                last_name=self.last_name,
                secret_code=self.secret_code,
            )
            LOGGER.debug(resp)
            self.user_secret = resp.data["userSecret"]

            return await self.async_step_box()

        return self.async_show_form(
            step_id="url", data_schema=URL_SCHEMA, errors=errors
        )

    async def async_step_box(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Setup Clever EVSE"""
        return True
