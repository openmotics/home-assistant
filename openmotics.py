"""
Support for OpenMotics.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/openmotics/
"""
import asyncio
import logging
import socket
from datetime import timedelta

import voluptuous as vol

from homeassistant.const import (
    CONF_HOST, CONF_PORT,
    CONF_USERNAME, CONF_PASSWORD)
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.discovery import async_load_platform
#from var_dump import var_dump
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['https://github.com/woutercoppens/openmoticssdk'
                '/archive/master.zip'
                '#openmoticssdk']

DOMAIN = 'openmotics'
OM_LOGIN = 'openmotics_login'
OM_LIGHTS = 'openmotics_lights'
OM_SWITCHES = 'openmotics_switches'
OM_SCENES = 'openmotics_scenes'
OM_OUTPUT_STATUS = 'openmotics_output_status'
OM_THERMOSTAT_STATUS = 'openmotics_thermostat_status'

OM_SWITCH_TYPE = 0
OM_LIGHT_TYPE = 255

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=15)

CONF_VERIFY_HTTPS = True

DEFAULT_HOST = 'cloud.openmotics.com'
DEFAULT_PORT = 443
DEFAULT_VERIFY_HTTPS = False


def is_socket_address(value):
    """Validate that value is a valid address."""
    try:
        socket.getaddrinfo(value, None)
        return value
    except OSError:
        raise vol.Invalid('Device is not a valid domain name or ip address')


CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Inclusive(CONF_USERNAME, 'auth'): cv.string,
        vol.Inclusive(CONF_PASSWORD, 'auth'): cv.string,
        vol.Optional(CONF_HOST, default=DEFAULT_HOST):
            #vol.All(cv.string, is_socket_address),
            cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_VERIFY_HTTPS,
                     default=DEFAULT_VERIFY_HTTPS): cv.boolean,
    })
}, extra=vol.ALLOW_EXTRA)


@asyncio.coroutine
def async_setup(hass, config):
    """Set up the OpenMotics components."""
    hass.data[OM_LOGIN] = OpenMoticsHub(hass, config)
    hub = hass.data[OM_LOGIN]
    if hub.get_status() is None:
        return False
    _LOGGER.info("Scanning for openmotics modules.")
    hub.get_modules()
    hub.get_scenes()
    hub.update()
    ''' inputs, output, shutters '''
    for component in ('switch', 'light', 'scene'):
        hass.async_add_job(async_load_platform(
            hass, component, DOMAIN, {}, config))
    return True


class OpenMoticsHub(Entity):
    """Thread safe wrapper class for openmotics python sdk."""

    def __init__(self, hass, config):
        """Initialize the openmotics hub."""
        from openmoticssdk import (AuthenticationException,
                                   MaintenanceModeException,
                                   ApiException)
        self._hass = hass
        self.my_openmotics = None

        host = config[DOMAIN][CONF_HOST]
        if host == DEFAULT_HOST:
            from openmoticssdk import OpenMoticsCloudApi
            self.my_openmotics = OpenMoticsCloudApi(config[DOMAIN][CONF_USERNAME],
                                                   config[DOMAIN][CONF_PASSWORD])
        else:
            from openmoticssdk import OpenMoticsApi
            self.my_openmotics = OpenMoticsApi(config[DOMAIN][CONF_USERNAME],
                                              config[DOMAIN][CONF_PASSWORD],
                                              config[DOMAIN][CONF_HOST],
                                              config[DOMAIN][CONF_VERIFY_HTTPS],
                                              config[DOMAIN][CONF_PORT])

    def get_status(self):
        """Initialize the openmotics hub."""
        try:
            ret = self.my_openmotics.get_status()
            return self._parse_output(ret)
        except (AuthenticationException,
                MaintenanceModeException,
                ApiException) as e:
            _LOGGER.error(e)
            return None

    def get_modules(self):
        """Get the OpenMotics Modules."""
        modules = []
        modules = self.my_openmotics.get_modules()
        for key, item in modules.items():
            if key == 'inputs':
                if item is not None:
                    _LOGGER.info("found input modules.")
            if key == 'outputs':
                if item is not None:
                    _LOGGER.info("found output modules.")
                    self._hass.data[OM_SWITCHES] = self.get_outputs(OM_SWITCH_TYPE)
                    self._hass.data[OM_LIGHTS] = self.get_outputs(OM_LIGHT_TYPE)
            if key == 'success':
                if item is True:
                    _LOGGER.info("getting modules was successful")
            if key == 'shutters':
                if item is not None:
                    _LOGGER.info("found shutters modules.")
        return True

    def get_scenes(self):
        """Get the openmotics group actions ."""
        _LOGGER.info("found shutters modules.")
        self._hass.data[OM_SCENES] = self.get_group_actions()

    def get_outputs(self, output_type):
        """Get the outputs."""
        outputs = []
        success, output_configs = self.get_output_configurations()
        if success is False:
            _LOGGER.error("Error getting output configurations")
            return outputs
        for output in output_configs['config']:
            if (output['name'] is None or output['name'] == ""):
                continue
            else:
                if output['type'] == output_type:
                    outputs.append(output)
        if not outputs:
            _LOGGER.debug("No outputs found with type %s", output_type)
        return outputs

    def get_output_configurations(self):
        """Get the output configurations."""
        try:
            ret = self.my_openmotics.get_output_configurations()
            return self._parse_output(ret)
        except (AuthenticationException,
                MaintenanceModeException,
                ApiException) as e:
            _LOGGER.error(e)
            return None
    
    def get_group_actions(self):
        """Get the outputs."""
        actions = []
        success, action_configs = self.get_group_action_configurations()
        if success is False:
            _LOGGER.error("Error getting group action configurations")
            return actions
        for action in action_configs['config']:
            if (action['name'] is None or action['name'] == ""):
                continue
            else:
                actions.append(action)
        if not actions:
            _LOGGER.debug("No group actions found")
        return actions

    def get_group_action_configurations(self):
        """Get the group action configurations."""
        try:
            ret = self.my_openmotics.get_group_action_configurations()
            return self._parse_output(ret)
        except (AuthenticationException,
                MaintenanceModeException,
                ApiException) as e:
            _LOGGER.error(e)
            return None

    #@Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update the status op the Openmotics modules."""
        self.update_status()

    def update_status(self):
        """Function to force an update of the modules.

        Can be called from within other components and will bypass throttle.
        """
        try:
            success1, output_status = self.get_output_status()
            if success1 is True:
                self._hass.data[OM_OUTPUT_STATUS] = output_status['status']
            success2, thermostat_status = self.get_thermostat_status()
            if success2 is True:
                self._hass.data[OM_THERMOSTAT_STATUS] = thermostat_status['status']
            if success1 and success2:
                _LOGGER.info("OpenMotics Controller data updated successfully")
            else:
                _LOGGER.error("OpenMotics Controller data updated failed")
        except (AuthenticationException,
                MaintenanceModeException,
                ApiException) as e:
            _LOGGER.error(e)
            return None

    def get_output_status(self):
        """Get the status of all the outputs."""
        try:
            ret = self.my_openmotics.get_output_status()
            return self._parse_output(ret)
        except (AuthenticationException,
                MaintenanceModeException,
                ApiException) as e:
            _LOGGER.error(e)
            return None

    def get_thermostat_status(self):
        """Get the status of all the thermostats."""
        try:
            ret = self.my_openmotics.get_thermostat_status()
            return self._parse_output(ret)
        except (AuthenticationException,
                MaintenanceModeException,
                ApiException) as e:
            _LOGGER.error(e)
            return None

    def set_output(self, id, status, dimmer, timer):
        """Set the status of an output."""
        so = self.my_openmotics.set_output(id, status, dimmer, timer)
        #var_dump(so)
        try:
            if so['success'] is True:
                return True
            else:
                _LOGGER.error("Error setting output id %s to %s", id, status)
                return False
        except KeyError:
            return False

    def do_group_action(self, id):
        """Execute a group action."""
        so = self.my_openmotics.do_group_action(id)
        #var_dump(so)
        try:
            if so['success'] is True:
                return True
            else:
                _LOGGER.error("Error executing group action id %s ", id)
                return False
        except KeyError:
            return False

    def _parse_output(self, dictionary):
        """Function to parse the json output."""
        data = {}
        try:
            success = dictionary['success']
            if success is False:
                return False, data
            for key, value in dictionary.items():
                if key == 'success':
                    continue
                data[key] = value
            return True, data

        except KeyError:
            return False, data
