"""The Openmotics integration.

    Support for OpenMotics.
    For more details about this component, please refer to the documentation at
    https://github.com/openmotics/home-assistant

    For examples of the output of the api, look at openmotics_api.md
"""
# pylint: disable=import-outside-toplevel
from __future__ import annotations

import logging

from homeassistant import config_entries, core
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_IP_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session

from .const import CONF_INSTALLATION_ID, DOMAIN, PLATFORMS, STARTUP_MESSAGE
from .coordinator import (
    OpenMoticsCloudDataUpdateCoordinator,
    OpenMoticsLocalDataUpdateCoordinator,
)
from .oauth_impl import OpenMoticsOauth2Implementation

CONF_AUTH_IMPLEMENTATION = "auth_implementation"

_LOGGER = logging.getLogger(__name__)


async def async_setup_openmotics_installation(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry, openmotics_installation
):
    """Set up the OpenMotics Installation."""
    device_registry = await dr.async_get_registry(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, openmotics_installation["id"])},
        manufacturer="OpenMotics",
        name=openmotics_installation["name"],
        model=openmotics_installation["gateway_model"],
        sw_version=openmotics_installation["version"],
    )

    return True


async def async_setup_entry(
    hass: core.HomeAssistant, entry: config_entries.ConfigEntry
):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    if CONF_IP_ADDRESS in entry.data:
        # Local gateway
        coordinator = OpenMoticsLocalDataUpdateCoordinator(
            hass,
            name=f"Localgw_{entry.data.get(CONF_IP_ADDRESS)}",
        )

    else:
        # Cloud
        implementation = OpenMoticsOauth2Implementation(
            hass,
            domain=entry.data.get(CONF_AUTH_IMPLEMENTATION),
            client_id=entry.data.get(CONF_CLIENT_ID),
            client_secret=entry.data.get(CONF_CLIENT_SECRET),
            name=entry.data.get(CONF_AUTH_IMPLEMENTATION),
        )
        oauth2_session = OAuth2Session(hass, entry, implementation)

        coordinator = OpenMoticsCloudDataUpdateCoordinator(
            hass,
            session=oauth2_session,
            name=entry.data.get(CONF_AUTH_IMPLEMENTATION),
        )

        coordinator.omclient.installation_id = entry.data.get(CONF_INSTALLATION_ID)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Spin up the platforms
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""

    # Unload entities for this entry/device.
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Cleanup
    if unload_ok:
        del hass.data[DOMAIN][entry.entry_id]

    return unload_ok
