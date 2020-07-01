"""Support for HomeAssistant shutters."""
# from var_dump import var_dump

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    CoverEntity,
)
from homeassistant.const import STATE_CLOSED, STATE_CLOSING, STATE_OPEN, STATE_OPENING
from homeassistant.core import callback
# from homeassistant.const import STATE_OFF, STATE_ON

from .const import (_LOGGER, DOMAIN, NOT_IN_USE)
# from .const import (_LOGGER, DOMAIN, OPENMOTICS_MODULE_TYPE_TO_NAME,
#                     OPENMOTICS_OUTPUT_TYPE_TO_NAME, NOT_IN_USE)
# from .util import get_key_for_word


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Component doesn't support configuration through configuration.yaml."""
    return


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Shutters for OpenMotics Controller."""
    entities = []

    om_cloud = hass.data[DOMAIN][config_entry.entry_id]

    om_installations = await hass.async_add_executor_job(om_cloud.installations)

    for install in om_installations:
        install_id = install.get('id')
        om_shutters = await hass.async_add_executor_job(om_cloud.shutters, install_id)
        if om_shutters:
            for om_shutter in om_shutters:
                if (om_shutter['name'] is None or om_shutter['name'] == "" or om_shutter['name'] == NOT_IN_USE):
                    continue
                # print("- {}".format(om_shutter))
                entities.append(OpenMoticsSwitch(hass, om_cloud, install, om_shutter))

    if not entities:
        _LOGGER.warning("No OpenMotics shutters added")
        return False

    async_add_entities(entities)


class OpenMoticsShutter(CoverEntity):
    """Representation of a OpenMotics shutter."""

    def __init__(self, hass, om_cloud, install, om_shutter):
        """Initialize the shutter."""
        self._hass = hass
        self.om_cloud = om_cloud
        self._install_id = install['id']
        self._device = om_shutter
        self._current_position = None

    @property
    def should_poll(self):
        """Enable polling."""
        return True

    @property
    def name(self):
        """Return the name of the light."""
        return self._device['name']

    @property
    def floor(self):
        """Return the floor of the light."""
        location = self._device['location']
        return location['floor_id']

    @property
    def room(self):
        """Return the room of the light."""
        location = self._device['location']
        return location['room_id']

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._device['id']

    @property
    def install_id(self):
        """Return the installation ID."""
        return self._install_id

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        if self.current_cover_position is None:
            return None
        return self.current_cover_position == 0

    @property
    def current_cover_position(self):
        """Return the current position of cover.
        None is unknown, 0 is closed, 100 is fully open.
        """
        return self._current_position

    @property
    def device_info(self):
        """Return information about the device."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "id": self.unique_id,
            "floor": self.floor,
            "room": self.room,
            "installation": self.install_id,
            "manufacturer": "OpenMotics",
        }

    async def async_open_cover(self, **kwargs):
        """Open the window cover."""
        await self.hass.async_add_executor_job(self.om_cloud.shutter_up, self.install_id, self.unique_id)

    async def async_close_cover(self, **kwargs):
        """Open the window cover."""
        await self.hass.async_add_executor_job(self.om_cloud.shutter_down, self.install_id, self.unique_id)

    async def async_stop_cover(self, **kwargs):
        """Stop the window cover."""
        await self.hass.async_add_executor_job(self.om_cloud.shutter_stop, self.install_id, self.unique_id)
