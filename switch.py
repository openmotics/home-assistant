"""Support for HomeAssistant switches."""
# from var_dump import var_dump

from homeassistant.components.switch import SwitchEntity
# import homeassistant.helpers.device_registry as dr
# from homeassistant.core import callback
from homeassistant.const import STATE_OFF, STATE_ON

from .const import (_LOGGER, DOMAIN, NOT_IN_USE)
# from .const import (_LOGGER, DOMAIN, OPENMOTICS_MODULE_TYPE_TO_NAME,
#                     OPENMOTICS_OUTPUT_TYPE_TO_NAME, NOT_IN_USE)
# from .util import get_key_for_word


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Component doesn't support configuration through configuration.yaml."""
    return


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Switches for OpenMotics Controller."""
    entities = []

    om_cloud = hass.data[DOMAIN][config_entry.entry_id]

    om_installations = await hass.async_add_executor_job(om_cloud.installations)

    for install in om_installations:
        install_id = install.get('id')
        om_outlets = await hass.async_add_executor_job(om_cloud.outlets, install_id)
        if om_outlets:
            for om_outlet in om_outlets:
                if (om_outlet['name'] is None or om_outlet['name'] == "" or om_outlet['name'] == NOT_IN_USE):
                    continue
                # print("- {}".format(om_outlet))
                entities.append(OpenMoticsSwitch(hass, om_cloud, install, om_outlet))

    if not entities:
        _LOGGER.warning("No OpenMotics Outlets added")
        return False

    async_add_entities(entities)


class OpenMoticsSwitch(SwitchEntity):
    """Representation of a OpenMotics switch."""

    def __init__(self, hass, om_cloud, install, om_switch):
        """Initialize the switch."""
        self._hass = hass
        self.om_cloud = om_cloud
        self._install_id = install['id']
        self._device = om_switch
        self._state = None

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
        """If switch is available."""
        return self._state is not None

    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        await self.hass.async_add_executor_job(self.om_cloud.output_turn_on, self.install_id, self.unique_id)

        self.async_update

    async def async_turn_off(self, **kwargs):
        """Turn devicee off."""
        await self.hass.async_add_executor_job(self.om_cloud.output_turn_off, self.install_id, self.unique_id)

        self.async_update

    async def async_update(self):
        """Update the state of the switch."""
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
        else:
            self._state = None
