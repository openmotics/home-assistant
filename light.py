""" Support for HomeAssistant lights. """
# from var_dump import var_dump

from homeassistant.components.light import (ATTR_BRIGHTNESS,
                                            SUPPORT_BRIGHTNESS, LightEntity)
from homeassistant.const import STATE_OFF, STATE_ON

from .const import (_LOGGER, DOMAIN, OPENMOTICS_MODULE_TYPE_TO_NAME,
                    OPENMOTICS_OUTPUT_TYPE_TO_NAME)
from .gateway import get_gateway_from_config_entry
from .util import get_key_for_word

# import homeassistant.helpers.device_registry as dr
# from homeassistant.core import callback



async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Component doesn't support configuration through configuration.yaml."""
    return


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Lights for OpenMotics Controller."""
    gateway = get_gateway_from_config_entry(hass, config_entry)

    entities = []
    om_lights = []

    light_type = get_key_for_word(OPENMOTICS_OUTPUT_TYPE_TO_NAME, 'light')
    for module in gateway.get_om_output_modules():
        if module['type'] == light_type:
            om_lights.append(module)

    if not om_lights:
        _LOGGER.debug("No lights found.")
        return False

    for entity in om_lights:
        _LOGGER.debug("Adding light %s", entity)
        entities.append(OpenMoticsLight(hass, gateway, entity))

    if not entities:
        _LOGGER.warning("No OpenMotics Lights added")
        return False

    async_add_entities(entities)


def brightness_to_percentage(byt):
    """Convert brightness from absolute 0..255 to percentage."""
    return round((byt * 100.0) / 255.0)


def brightness_from_percentage(percent):
    """Convert percentage to absolute value 0..255."""
    return round((percent * 255.0) / 100.0)


class OpenMoticsLight(LightEntity):
    """Representation of a OpenMotics light."""

    def __init__(self, hass, gateway, light):
        """Initialize the light."""
        self._hass = hass
        self.gateway = gateway
        self._id = light['id']
        self._name = light['name']
        self._floor = light['floor']
        self._room = light['room']
        self._module_type = light['module_type']
        self._type = light['type']
        self._timer = None
        self._dimmer = None
        self._state = None

        self._refresh()

    @property
    def supported_features(self):
        """Flag supported features."""
        # Check if the light's module is a Dimmer, return brightness as a supported feature.
        if self._module_type == get_key_for_word(OPENMOTICS_MODULE_TYPE_TO_NAME, 'Dimmer'):
            return SUPPORT_BRIGHTNESS

        return 0

    # @property
    # def should_poll(self):
    #     """Enable polling."""
    #     return True

    @property
    def name(self):
        """Return the name of the light."""
        return self._name

    @property
    def floor(self):
        """Return the floor of the light."""
        return self._floor

    @property
    def room(self):
        """Return the room of the light."""
        return self._room

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._id

    @property
    def is_on(self):
        """Return true if device is on."""
        return self._state == STATE_ON

    @property
    def device_info(self):
        """Return information about the device."""
        info = {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "id": self.unique_id,
            "floor": self.floor,
            "room": self.room,
            "manufacturer": "OpenMotics",
        }
        return info

    @property
    def available(self):
        """If light is available."""
        return self._state is not None

    @property
    def brightness(self) -> int:
        """Return the brightness of this light between 0..255."""
        # brightness = int(self._dimmer * BRIGHTNESS_SCALE_UP)
        # :type dimmer: Integer [0, 100] or None
        if self._dimmer is None:
            return 0

        return brightness_from_percentage(self._dimmer)

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        brightness = 0
        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
        else:
            if self._dimmer is not None:
                brightness = brightness_from_percentage(self._dimmer)
            if brightness == 0:
                brightness = 255

        self._dimmer = brightness_to_percentage(brightness)

        sop = await self._hass.async_add_executor_job(self.gateway.api.set_output, self._id, True, self._dimmer, self._timer)
        if sop['success'] is True:
            self._state = STATE_ON
        else:
            _LOGGER.error("Error setting output id %s to True", self._id)
            self._state = STATE_OFF

    async def async_turn_off(self, **kwargs):
        """Turn devicee off."""
        sop = await self._hass.async_add_executor_job(self.gateway.api.set_output, self._id, False, None, None)
        if sop['success'] is True:
            self._state = STATE_OFF
        else:
            _LOGGER.error("Error setting output id %s to False", self._id)
            self._state = STATE_ON

    async def async_update(self):
        """Retrieve latest state."""
        await self._hass.async_add_executor_job(self._refresh)

    def _refresh(self):
        """Refresh the state of the light."""
        if not self.gateway.update() and self._state is not None:
            return

        output_status = self.gateway.get_output_status(self._id)
        # {'status': 1, 'dimmer': 100, 'ctimer': 0, 'id': 66}

        if not output_status:
            _LOGGER.error('Light._refresh: No responce form the controller')
            return

        if output_status['dimmer'] is not None:
            self._dimmer = output_status['dimmer']

        if output_status['ctimer'] is not None:
            self._ctimer = output_status['ctimer']

        if output_status['status'] is not None:
            if output_status['status'] == 1:
                self._state = STATE_ON
            else:
                self._state = STATE_OFF
        else:
            self._state = None
