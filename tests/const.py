"""Constants for weenect tests."""
from typing import Any

from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_VERIFY_SSL,
)

from custom_components.openmotics.const import CONF_INSTALLATION_ID

# Mock config data to be used across multiple tests
CLOUD_MOCK_CONFIG: dict[str, Any] = {
    CONF_CLIENT_ID: "abcd",
    CONF_CLIENT_SECRET: "efgh",
    CONF_INSTALLATION_ID: 1,
}

LOCALGW_MOCK_CONFIG: dict[str, Any] = {
    CONF_IP_ADDRESS: "127.0.0.2",
    CONF_NAME: "abcd",
    CONF_PASSWORD: "efgh",
    CONF_PORT: 443,
    CONF_VERIFY_SSL: True,
}
