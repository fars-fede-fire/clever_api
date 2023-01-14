"""Config flow for Clever API integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries, exceptions, core
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN  # pylint:disable=unused-import
from .login import Login

_LOGGER = logging.getLogger(__name__)

# This is the schema that used to display the UI to the user. This simple
# schema has a single required host field, but it could include a number of fields
# such as username, password etc. See other components in the HA core code for
# further examples.
# Note the input displayed to the user will be translated. See the
# translations/<lang>.json file and strings.json. See here for further information:
# https://developers.home-assistant.io/docs/config_entries_config_flow_handler/#translations
# At the time of writing I found the translations created by the scaffold didn't
# quite work as documented and always gave me the "Lokalise key references" string
# (in square brackets), rather than the actual translated value. I did not attempt to
# figure this out or look further into it.
DATA_SCHEMA = vol.Schema({vol.Optional("email"): str})
URL_SCHEMA = vol.Schema({vol.Optional("email"): str, vol.Required("url"): str})


async def send_email(data, hass):
    """Request login email from Clever"""
    session = async_get_clientsession(hass)
    login = Login(session, data["email"])
    await login.request_login_email()
    return {"title": data["email"]}


async def obtain_api_key(data, hass):
    """Exchange login url to API key."""
    session = async_get_clientsession(hass)
    login = Login(session, data["email"])
    api_key = await login.exchange_secretCode(data["url"])
    return api_key


class CleverAPIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Clever API."""

    VERSION = 1
    # Pick one of the available connection classes in homeassistant/config_entries.py
    # This tells HA if it should be asking for updates, or it'll be notified of updates
    # automatically. This example uses PUSH, as the dummy hub will notify HA of
    # changes.

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        # This goes through the steps to take the user through the setup process.
        # Using this it is possible to update the UI and prompt for additional
        # information. This example provides a single form (built from `DATA_SCHEMA`),
        # and when that has some validated input, it calls `async_create_entry` to
        # actually create the HA config entry. Note the "title" value is returned by
        # `validate_input` above.
        errors = {}
        if user_input is not None:
            try:
                await send_email(user_input, self.hass)
                self.data = user_input
                self.data["email"] = []
                return await self.async_step_url()

            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                # The error string is set here, and should be translated.
                # This example does not currently cover translations, see the
                # comments on `DATA_SCHEMA` for further details.
                # Set the error on the `host` field, not the entire form.
                errors["host"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )

    async def async_step_url(self, user_input=None):
        if user_input is not None:
            api_key = await obtain_api_key(user_input, self.hass)
            user_input["api_key"] = api_key
            return self.async_create_entry(title="Clever API", data=user_input)

        return self.async_show_form(step_id="url", data_schema=URL_SCHEMA)


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
