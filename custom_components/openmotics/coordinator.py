"""DataUpdateCoordinator for the OpenMotics integration."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.const import (
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_VERIFY_SSL,
)
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pyhaopenmotics import (
    LocalGateway,
    OpenMoticsCloud,
    OpenMoticsError,
    get_ssl_context,
)

from .const import CONF_INSTALLATION_ID, DEFAULT_SCAN_INTERVAL, DOMAIN

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.config_entry_oauth2_flow import OAuth2Session

_LOGGER = logging.getLogger(__name__)


class OpenMoticsDataUpdateCoordinator(DataUpdateCoordinator):
    """Query OpenMotics devices and keep track of seen conditions."""

    def __init__(self, hass: HomeAssistant, *, name: str) -> None:
        """Initialize the OpenMotics gateway."""
        super().__init__(
            hass=hass,
            logger=_LOGGER,
            name=name or DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.session = None
        self._omclient: OpenMoticsCloud | LocalGateway
        self._install_id = None

    async def _async_update_data(self) -> dict[Any, Any]:
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            my_outputs = await self._omclient.outputs.get_all()
            my_lights = await self._omclient.lights.get_all()
            my_groupactions = await self._omclient.groupactions.get_all()
            my_shutters = await self._omclient.shutters.get_all()
            my_sensors = await self._omclient.sensors.get_all()
            my_thermostatgroups = await self._omclient.thermostats.groups.get_all()
            my_thermostatunits = await self._omclient.thermostats.units.get_all()
            if hasattr(self._omclient, "energysensors"):
                my_energysensors = await self._omclient.energysensors.get_all()
            else:
                my_energysensors = []

        except OpenMoticsError as err:
            _LOGGER.error("Could not retrieve the data from the OpenMotics API")
            _LOGGER.error("Too many errors: %s", err)
            return {
                "lights": [],
                "outputs": [],
                "groupactions": [],
                "shutters": [],
                "sensors": [],
                "energysensors": [],
                "thermostatgroups": [],
                "thermostatunits": [],
            }
        # Store data in a way Home Assistant can easily consume it
        return {
            "outputs": my_outputs,
            "lights": my_lights,
            "groupactions": my_groupactions,
            "shutters": my_shutters,
            "sensors": my_sensors,
            "energysensors": my_energysensors,
            "thermostatgroups": my_thermostatgroups,
            "thermostatunits": my_thermostatunits,
        }

    @property
    def omclient(self) -> Any:
        """Return the backendclient."""
        return self._omclient

    @property
    def install_id(self) -> Any:
        """Return the backendclient."""
        return self._install_id


class OpenMoticsCloudDataUpdateCoordinator(OpenMoticsDataUpdateCoordinator):
    """Query OpenMotics devices and keep track of seen conditions."""

    def __init__(self, hass: HomeAssistant, session: OAuth2Session, name: str) -> None:
        """Initialize the OpenMotics gateway."""
        super().__init__(
            hass=hass,
            name=name,
        )
        self.session = session
        self._install_id = self.config_entry.data.get(CONF_INSTALLATION_ID)

        async def async_token_refresh() -> Any:
            await session.async_ensure_token_valid()
            return session.token["access_token"]

        self._omclient = OpenMoticsCloud(
            token=session.token["access_token"],
            session=async_get_clientsession(hass),
            token_refresh_method=async_token_refresh,
        )


class OpenMoticsLocalDataUpdateCoordinator(OpenMoticsDataUpdateCoordinator):
    """Query OpenMotics devices and keep track of seen conditions."""

    def __init__(self, hass: HomeAssistant, name: str) -> None:
        """Initialize the OpenMotics gateway."""
        super().__init__(
            hass=hass,
            name=name,
        )
        self._install_id = self.config_entry.data.get(CONF_IP_ADDRESS)
        ssl_context = get_ssl_context(self.config_entry.data.get(CONF_VERIFY_SSL))

        """Set up a OpenMotics controller"""
        self._omclient = LocalGateway(
            localgw=self.config_entry.data.get(CONF_IP_ADDRESS),
            username=self.config_entry.data.get(CONF_NAME),
            password=self.config_entry.data.get(CONF_PASSWORD),
            port=self.config_entry.data.get(CONF_PORT),
            ssl_context=ssl_context,
        )
