"""
Support for OpenMotics Switches.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/switch.openmotics/
"""
import logging

#from homeassistant.components.openmotics import (OM_LOGIN, OM_LIGHTS, OM_OUTPUT_STATUS)
from custom_components.openmotics import (OM_LOGIN, OM_LIGHTS, OM_OUTPUT_STATUS,
                                          OM_OUTPUT_DIMMER)
from homeassistant.components.light import (ATTR_BRIGHTNESS,
                                            SUPPORT_BRIGHTNESS, Light)

# from var_dump import var_dump

DEPENDENCIES = ['openmotics']

BRIGHTNESS_SCALE_UP = 2.55
BRIGHTNESS_SCALE_DOWN = 0.3925
NOT_IN_USE = "NOT_IN_USE"

_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Register connecter outputs."""
    lights = []

    if discovery_info is None:
        return
    for dev in hass.data[OM_LIGHTS]:
        if (dev['name'] is None or dev['name'] == ""):
            continue
        else:
            _LOGGER.debug("Adding lights %s", dev)
            lights.append(OpenMoticsLight(hass, dev))
    if not lights:
        _LOGGER.error("No OpenMotics Switches added")
        return False

    async_add_devices(lights)
    return True

class OpenMoticsLight(Light):
    """Representation of a OpenMotics light."""

    def __init__(self, hass, light):
        """Initialize the light."""
        self._hass = hass
        self.hub = hass.data[OM_LOGIN]
        self._id = light['id']
        self._name = light['name']
        self._floor = light['floor']
        self._room = light['room']
        self._module_type = light['module_type']
        self._timer = None
        self._dimmer = None
        self._state = None

        self.update()

    @property
    def hidden(self):
        """Return True if the entity should be hidden from UIs."""
        return self._name == NOT_IN_USE

    @property
    def supported_features(self):
        """Flag supported features."""
        """Check if the light's module is a Dimmer, return brightness as a supported feature."""
        if self._module_type == OM_OUTPUT_DIMMER:
            return SUPPORT_BRIGHTNESS
        else:
            return 0

    @property
    def name(self):
        """Return the name of the light."""
        return self._name

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._state

    @property
    def available(self):
        """If light is available."""
        return self._state is not None

    @property
    def brightness(self):
        """Return the brightness of this light between 0..100."""
        brightness = int(self._dimmer * BRIGHTNESS_SCALE_UP)
        return brightness

    def turn_on(self, **kwargs):
        """Turn device on."""
        if ATTR_BRIGHTNESS in kwargs:
            brightness = int(kwargs[ATTR_BRIGHTNESS] * BRIGHTNESS_SCALE_DOWN)
            self._dimmer = brightness
        if self.hub.set_output(self._id, True, self._dimmer, self._timer):
            self.hub.force_update()
            self._state = True

    def turn_off(self, **kwargs):
        """Turn devicee off."""
        if self.hub.set_output(self._id, False, None, None):
            self.hub.force_update()
            self._state = False

    def update(self):
        """Update the state of the light."""
        self.hub.update()
        output_statuses = self._hass.data[OM_OUTPUT_STATUS]
        if not output_statuses:
            _LOGGER.error('No responce form the controller')
            return
        for output_status in output_statuses:
            if output_status['id'] == self._id:
                if output_status['dimmer'] is not None:
                    self._dimmer = output_status['dimmer']
                if output_status['ctimer'] is not None:
                    self._ctimer = output_status['ctimer']
                if output_status['status'] is not None:
                    if output_status['status'] == 1:
                        self._state = True
                    else:
                        self._state = False
                else:
                    self._state = None
