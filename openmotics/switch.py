"""
Support for OpenMotics Switches.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/switch.openmotics/
"""
import logging

#from homeassistant.components.openmotics import (OM_LOGIN, OM_SWITCHES, OM_OUTPUT_STATUS)
from custom_components.openmotics import (OM_LOGIN, OM_SWITCHES, OM_OUTPUT_STATUS)
from homeassistant.components.switch import SwitchDevice

# from var_dump import var_dump

DEPENDENCIES = ['openmotics']

_LOGGER = logging.getLogger(__name__)

# _VALID_TIMER = [150, 450, 900, 1500, 2220, 3120]


def setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Register connecter outputs."""
    switches = []

    if discovery_info is None:
        return
    for dev in hass.data[OM_SWITCHES]:
        if (dev['name'] is None or dev['name'] == ""):
            continue
        else:
            _LOGGER.debug("Adding switches %s", dev)
            switches.append(OpenMoticsSwitch(hass, dev))
    if not switches:
        _LOGGER.error("No OpenMotics Switches added")
        return False

    async_add_devices(switches)
    return True


class OpenMoticsSwitch(SwitchDevice):
    """Representation of a OpenMotics switch."""

    def __init__(self, hass, switch):
        """Initialize the switch."""
        self._hass = hass
        self.hub = hass.data[OM_LOGIN]
        self._id = switch['id']
        self._name = switch['name']
        self._floor = switch['floor']
        self._room = switch['room']
        self._timer = None
        self._dimmer = None
        self._state = None

        self.update()

    @property
    def name(self):
        """Return the name of the switch."""
        return self._name

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._state

    @property
    def available(self):
        """If switch is available."""
        return self._state is not None

    def turn_on(self, **kwargs):
        """Turn device on."""
        if self.hub.set_output(self._id, True, self._dimmer, self._timer):
            self._state = True

    def turn_off(self, **kwargs):
        """Turn devicee off."""
        if self.hub.set_output(self._id, False, None, None):
            self._state = False

    def update(self):
        """Update the state of the switch."""
        if not self.hub.update() and self._state is not None:
            return
        output_statuses = self._hass.data[OM_OUTPUT_STATUS]
        if not output_statuses:
            _LOGGER.error('No responce form the controller')
            return
        for output_status in output_statuses:
            if output_status['id'] == self._id:
                if output_status['dimmer'] is not None:
                    self._dimmer = output_status['dimmer']
                if output_status['status'] is not None:
                    if output_status['status'] == 1:
                        self._state = True
                    else:
                        self._state = False
                else:
                    self._state = None
