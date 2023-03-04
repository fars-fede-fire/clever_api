"""Constants for Clever API integration."""
from __future__ import annotations

import logging

from typing import Final


DOMAIN: Final = "clever_api"

LOGGER = logging.getLogger(__package__)

CONF_URL = "url"
CONF_BOX = "box"
CONF_BOX_ID = "box_id"
CONF_CONNECTOR_ID = "box_connector_id"
CONF_SUBSCRIPTION_FEE = "subscription_fee"
