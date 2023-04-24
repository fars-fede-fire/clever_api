"""Constants for Clever API integration."""
from __future__ import annotations

import logging
from typing import Final

DOMAIN: Final = "clever_api"

LOGGER = logging.getLogger(__package__)

CONF_URL = "url"
CONF_USER_ID = "user_id"
CONF_BOX = "box"
CONF_BOX_ID = "box_id"
CONF_CONNECTOR_ID = "box_connector_id"
CONF_SUBSCRIPTION_FEE = "subscription_fee"
CONF_DEPT_TIME = "depature_time"
CONF_DESIRED_RANGE = "desired_range"
CONF_PHASE_COUNT = "phase_count"

SERVICE_ENABLE_FLEX = "enable_flex"
SERVICE_DISABLE_FLEX = "disable_flex"
