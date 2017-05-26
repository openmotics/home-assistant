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
from var_dump import var_dump
import homeassistant.helpers.config_validation as cv

_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['https://github.com/woutercoppens/openmoticssdk'
                '/archive/master.zip'
                '#openmoticssdk']

DOMAIN = 'openmotics'
OM_LOGIN = 'openmotics_login'
OM_LIGHTS = 'openmotics_lights'
OM_SWITCHES = 'openmotics_switches'
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

    hass.data[OM_LOGIN] = OpenMoticsHub(hass, config)
    hub = hass.data[OM_LOGIN]
    if hub.get_status() is None:
        return False
    _LOGGER.info("Scanning for openmotics modules.")
    hub.get_modules()
    hub.update()
    ''' inputs, output, shutters '''
    for component in ('switch', 'light'):
        hass.async_add_job(async_load_platform(
            hass, component, DOMAIN, {}, config))
    return True

class OpenMoticsHub(Entity):
    """Thread safe wrapper class for openmotics python sdk"""

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

    def get_outputs(self, output_type):
        outputs = []
        output_configs = self.get_output_configurations()
        if output_configs is None:
            return None
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
        ret = self.my_openmotics.get_output_configurations()
        return self._parse_output(ret)

    #@Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        self.update_status()

    def update_status(self):
        output_status = self.get_output_status()
        self._hass.data[OM_OUTPUT_STATUS] = output_status['status']
        #thermostat_status = self.get_thermostat_status()
        #self._hass.data[OM_THERMOSTAT_STATUS] = thermostat_status['status']
        _LOGGER.info("OpenMotics Controller data updated successfully")

    def get_output_status(self):
        ret = self.my_openmotics.get_output_status()
        return self._parse_output(ret)

    def get_thermostat_status(self):
        ret = self.my_openmotics.get_thermostat_status()
        return self._parse_output(ret)

    def set_output(self, id, status, dimmer, timer):
        so = self.my_openmotics.set_output(id, status, dimmer, timer)
        var_dump(so)
        try:
            if  so['success'] == True:
                return True
            else:
                _LOGGER.error("Error setting output id %s to %s", id, status)
                return False
        except KeyError:
            return False

    def _parse_output(self, dictionary):
        data = {}
        try:
            success = dictionary['success']
            if success == False:
                _LOGGER.error("Error calling api")
                return None
            for key, value in dictionary.items():
                if key == 'success':
                    continue
                data[key] = value
            return data

        except KeyError:
            return None
