"""Constants for OpenMotics integration."""
from datetime import timedelta

from homeassistant.const import Platform

# Base component constants
NAME = "OpenMotics Integration"
ATTR_MANUFACTURER = "OpenMotics"
DOMAIN = "openmotics"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.1"
ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"
ISSUE_URL = "https://github.com/openmotics/home-assistant/issues"

NOT_IN_USE = "NOT_IN_USE"

ENV_CLOUD = "cloud"
ENV_LOCAL = "local"


# The state of a light is refreshed every 30 seconds (more or less).
# Setting the interval between updates to 30 seconds was just a little bit
# to late. 28 seconds is better.
DEFAULT_SCAN_INTERVAL = timedelta(seconds=30)

PLATFORMS = [
    # Platform.BINARY_SENSORa
    Platform.CLIMATE,
    Platform.SWITCH,
    Platform.COVER,
    Platform.LIGHT,
    Platform.SENSOR,
    Platform.SCENE,
]

PRESET_AUTO = "auto"
PRESET_PARTY = "party"
PRESET_MANUAL = "manual"
PRESET_VACATION = "vacantion"

# Configuration and options
CONF_ENABLED = "enabled"
CONF_INSTALLATION_ID = "installation_id"

# Defaults
DEFAULT_NAME = DOMAIN

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
