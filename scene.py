""" Support for HomeAssistant scenes (aka group actions). """
# from var_dump import var_dump
from typing import Any
from homeassistant.components.scene import Scene
from homeassistant.core import callback
from .const import (_LOGGER, DOMAIN, NOT_IN_USE)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Component doesn't support configuration through configuration.yaml."""
    return


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Scenes for OpenMotics Controller."""
    entities = []

    om_cloud = hass.data[DOMAIN][config_entry.entry_id]

    om_installations = await hass.async_add_executor_job(om_cloud.installations)

    for install in om_installations:
        install_id = install.get('id')
        om_scenes = await hass.async_add_executor_job(om_cloud.groupactions, install_id)
        if om_scenes:
            for om_scene in om_scenes:
                if (om_scene['name'] is None or om_scene['name'] == "" or om_scene['name'] == NOT_IN_USE):
                    continue
                # print("- {}".format(om_scene))
                entities.append(OpenMoticsScene(hass, om_cloud, install, om_scene))

    if not entities:
        _LOGGER.warning("No OpenMotics scenes added")
        return False

    async_add_entities(entities)


class OpenMoticsScene(Scene):
    """Representation of a OpenMotics group action."""

    def __init__(self, hass, om_cloud, install, om_scene):
        """Initialize the scene."""
        self._hass = hass
        self.om_cloud = om_cloud
        self._install_id = install['id']
        self._device = om_scene

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

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        await self.hass.async_add_executor_job(self.om_cloud.trigger_scene, self.install_id, self.unique_id)