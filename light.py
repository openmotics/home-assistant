"""Support for HomeAssistant lights."""
# from var_dump import var_dump

from homeassistant.components.light import (ATTR_BRIGHTNESS,
                                            SUPPORT_BRIGHTNESS, LightEntity)
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import callback

from .const import (_LOGGER, DOMAIN, NOT_IN_USE)
# from .const import (_LOGGER, DOMAIN, OPENMOTICS_MODULE_TYPE_TO_NAME,
#                     OPENMOTICS_OUTPUT_TYPE_TO_NAME, NOT_IN_USE)
# from .gateway import get_gateway_from_config_entry
# from .util import get_key_for_word

# import homeassistant.helpers.device_registry as dr
# from homeassistant.core import callback


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Component doesn't support configuration through configuration.yaml."""
    return


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Lights for OpenMotics Controller."""
    entities = []

    om_cloud = hass.data[DOMAIN][config_entry.entry_id]

    om_installations = await hass.async_add_executor_job(om_cloud.installations)

    for install in om_installations:
        install_id = install.get('id')
        om_lights = await hass.async_add_executor_job(om_cloud.lights, install_id)
        if om_lights:
            for om_light in om_lights:
                if (om_light['name'] is None or om_light['name'] == "" or om_light['name'] == NOT_IN_USE):
                    continue
                # print("- {}".format(om_light))
                entities.append(OpenMoticsLight(hass, om_cloud, install, om_light))

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

    def __init__(self, hass, om_cloud, install, om_light):
        """Initialize the light."""
        self._hass = hass
        self.om_cloud = om_cloud
        self._install_id = install['id']
        self._device = om_light
        self._brightness: Optional[int] = None
        self._state: bool = False

    @property
    def supported_features(self):
        """Flag supported features."""
        # Check if the light's module is a Dimmer, return brightness as a supported feature.
        if 'RANGE' in self._device['capabilities']:
            return SUPPORT_BRIGHTNESS

        return 0

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
    def is_on(self):
        """Return true if device is on."""
        return self._state == STATE_ON

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

    @property
    def available(self):
        """If light is available."""
        return self._state is not None

    @property
    def brightness(self):
        """Return the brightness of this light."""
        return self._brightness

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        value: Optional[int] = None
        brightness = kwargs.get(light.ATTR_BRIGHTNESS)
        if brightness is not None:
                value = brightness_to_percentage(brightness)

        response = await self.hass.async_add_executor_job(self.om_cloud.output_turn_on, self.install_id, self.unique_id, brightness)

        # Turns on a specified Output object.
        # The call can optionally receive a JSON object that states the value in case the Output is dimmable.
        if response:
            try:
                self._brightness = brightness_from_percentage(responce['value'])
            except KeyError:
                self._brightness = None
        self.async_update

    async def async_turn_off(self, **kwargs):
        """Turn devicee off."""
        response = await self.hass.async_add_executor_job(self.om_cloud.output_turn_off, self.install_id, self.unique_id)

        self.async_update

    async def async_update(self):
        """Refresh the state of the light."""
        output_status = await self.hass.async_add_executor_job(self.om_cloud.output_by_id, self.install_id, self.unique_id)

        if not output_status:
            _LOGGER.error('Light._refresh: No responce form the controller')
            return
        # print("- {}".format(output_status))

        if output_status['status'] is not None:
            status = output_status['status']
            if status['on'] is True:
                self._state = STATE_ON
            else:
                self._state = STATE_OFF
            # if a light is not dimmable, the value field is not present.
            try:
                self._brightness = brightness_from_percentage(status['value'])
            except KeyError:
                self._brightness = None
        else:
            self._state = None
