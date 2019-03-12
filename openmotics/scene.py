"""
Support for openmotics group actions as scenes.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/scene.openmotics/
"""
import logging

from custom_components.openmotics import (OM_LOGIN, OM_SCENES)
from homeassistant.components.scene import Scene

DEPENDENCIES = ['openmotics']

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Register the openmotics group actions as scenes."""
    scenes = []

    if discovery_info is None:
        return
    for scene in hass.data[OM_SCENES]:
        if (scene['name'] is None or scene['name'] == ""):
            continue
        else:
            _LOGGER.debug("Adding openmotics group action %s", scene)
            scenes.append(OpenMoticsScene(hass, scene))
    if not scenes:
        _LOGGER.error("No OpenMotics group actions added")
        return False

    async_add_devices(scenes)
    return True


class OpenMoticsScene(Scene):
    """Representation of an Openmotics Group Action."""

    def __init__(self, hass, scene):
        """Init openmotics group action."""
        _LOGGER.info("Adding openmotics group action: %s", scene['name'])
        self._hass = hass
        self.hub = hass.data[OM_LOGIN]
        self._id = scene['id']
        self._name = scene['name']

    @property
    def name(self):
        """Return the name of the scene."""
        return self._name

    def activate(self):
        """Activate the scene."""
        self.hub.do_group_action(self._id)
        self.hub.force_update()
