"""
OpenMotics Gateway abstraction
"""
import asyncio
# from .util import get_key_for_word
# import time

import async_timeout

from homeassistant.const import (CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_PORT,
                                 CONF_HOST, CONF_VERIFY_SSL)
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity import Entity
from homeassistant.config_entries import ConfigEntry

from .const import (_LOGGER, DEFAULT_HOST, DOMAIN, MIN_TIME_BETWEEN_UPDATES,
                    NOT_IN_USE)
from .errors import AuthenticationRequired, CannotConnect
# from .openmoticssdk import (ApiException, AuthenticationException,
#                             MaintenanceModeException)

from openmotics.clients.cloud import BackendClient, APIError, LegacyClient
# from var_dump import var_dump

@callback
def get_gateway_from_config_entry(hass, config_entry):
    """Return gateway with a matching bridge id."""
    return hass.data[DOMAIN].get(config_entry.unique_id)


class OpenMoticsCloud:
    """Thread safe wrapper class for openmotics python sdk."""

    def __init__(
        self,
        hass: core.HomeAssistant,
        config_entry: config_entries.ConfigEntry,
    ):
        """Initialize the openmotics hub."""
        self.hass = hass
        self.config = config

        # self._installations = None

    @property
    def installations(self) -> bool:
        """Return the installations."""
        return self._installations

    # async def async_update_device_registry(self):
    #     """Update device registry."""
    #     device_registry = await self.hass.helpers.device_registry.async_get_registry()
    #     device_registry.async_get_or_create(
    #         config_entry_id=self.config_entry.entry_id,
    #         identifiers={(DOMAIN, self.bridgeid())},
    #         manufacturer="OpenMotics",
    #         sw_version=self.version(),
    #         gw_verion=self.gateway_version(),
    #     )

    async def async_setup(self):
        """Set up a OpenMotics controller"""
        if self.config[CONF_HOST] == DEFAULT_HOST:
            om_cloud = BackendClient(
                self.config[CONF_CLIENT_ID],
                self.config[CONF_CLIENT_SECRET],
                )
        else:
            om_cloud = BackendClient(
                self.config[CONF_CLIENT_ID],
                self.config[CONF_CLIENT_SECRET],
                server=self.config[CONF_HOST],
                port=self.config[CONF_PORT],
                ssl=self.config[CONF_VERIFY_SSL]
                )

        try:
            with async_timeout.timeout(15):
                om_cloud.get_token()

        except asyncio.TimeoutError:
            _LOGGER.error(
                "Timeout connecting to the OpenMoticsApi at %s",
                self.config[CONF_HOST]
                )
            raise CannotConnect

        except APIError:
            _LOGGER.error(
                "Error connecting to the OpenMoticsApi at %s",
                self.config[CONF_HOST]
                )
            _LOGGER.error(err)
            raise CannotConnect

        self._installations = om_cloud.installations()

        return True

    @staticmethod
    async def async_config_entry_updated(hass, entry):
        """Handle signals of config entry being updated.
        This is a static method because a class method (bound method), can not be used with weak references.
        Causes for this is either discovery updating host address or config entry options changing.
        """
        gateway = get_gateway_from_config_entry(hass, entry)
        if not gateway:
            return
        if gateway.api.host != entry.data[CONF_HOST]:
            # TODO
            # gateway.api.close()
            # gateway.api.host = entry.data[CONF_HOST]
            # gateway.api.start()
            return

        # await gateway.options_updated()

