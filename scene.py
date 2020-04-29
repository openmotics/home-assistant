""" Support for HomeAssistant scenes (aka group actions). """
# from var_dump import var_dump

from homeassistant.components.scene import Scene

from .const import _LOGGER
from .gateway import get_gateway_from_config_entry

# import homeassistant.helpers.device_registry as dr
# from homeassistant.core import callback

# from .util import get_key_for_word


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Component doesn't support configuration through configuration.yaml."""
    return


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Scenes for OpenMotics Controller."""
    gateway = get_gateway_from_config_entry(hass, config_entry)

    entities = []

    om_scenes = gateway.get_scenes()

    if not om_scenes:
        return False

    for entity in om_scenes:
        _LOGGER.debug("Adding scene %s", entity)
        entities.append(OpenMoticsScene(hass, gateway, entity))

    if not entities:
        _LOGGER.warning("No OpenMotics Scene added")
        return False

    async_add_entities(entities)


class OpenMoticsScene(Scene):
    """Representation of a OpenMotics group action."""

    def __init__(self, hass, gateway, scene):
        """Initialize the switch."""
        self._hass = hass
        self.gateway = gateway
        self._id = scene['id']
        self._name = scene['name']
        self._actions = scene['actions']
        self._timer = None
        self._dimmer = None
        self._state = None

    @property
    def name(self):
        """Return the name of the scene."""
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._id

    # @property
    # def device_info(self):
    #     """Return information about the device."""
    #     info = {
    #         "identifiers": {(DOMAIN, self.unique_id)},
    #         "name": self.name,
    #         "id" : self.unique_id,
    #         "floor" : self.floor,
    #         "room" : self.room,
    #         "manufacturer": "OpenMotics",
    #     }
    #     return info

    def activate(self):
        """Activate the scene."""
        dga = self.gateway.api.do_group_action(self._id)
        if dga['success'] is False:
            _LOGGER.error("Error doing group action with id %s ", self._id)
            return False
        return True
