"""
OpenMotics Gateway abstraction
"""
import asyncio
# from .util import get_key_for_word
import time
from threading import Lock

import async_timeout

from homeassistant.const import (CONF_HOST, CONF_PASSWORD, CONF_PORT,
                                 CONF_USERNAME, CONF_VERIFY_SSL)
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (_LOGGER, DEFAULT_HOST, DOMAIN, MIN_TIME_BETWEEN_UPDATES,
                    NOT_IN_USE)
from .errors import AuthenticationRequired, CannotConnect
from .openmoticssdk import (ApiException, AuthenticationException,
                            MaintenanceModeException)

# from var_dump import var_dump


# from .modules import OpenMoticsOutputModuleEntity

# Note: the python openmotics hasn't been updated the last 3 years
# I have included a copy in the custom_components because it was easier
# Otherwise I had to write a pyopenmotics dependency.
# REQUIREMENTS = ['https://github.com/woutercoppens/openmoticssdk'
#                '/archive/master.zip'
#                '#openmoticssdk']
# End sdk


@callback
def get_gateway_from_config_entry(hass, config_entry):
    """Return gateway with a matching bridge id."""
    return hass.data[DOMAIN].get(config_entry.unique_id)


class OpenMoticsGateway:
    """Thread safe wrapper class for openmotics python sdk."""

    def __init__(self, hass, config_entry):
        """Initialize the openmotics hub."""
        self.hass = hass
        self.config_entry = config_entry

        self.api = None

        # store the modules and status
        self.om_output_modules = []
        self.om_input_modules = []
        self.om_shutters = []
        self.om_can_imputs = []
        self.om_scenes = []
        self.om_outputs_status = []
        self.om_thermostats_status = []

        self.last_update_time = None
        self.mutex = Lock()

    @property
    def bridgeid(self) -> str:
        """Return the unique identifier of the gateway."""
        return self.config_entry.unique_id

    @property
    def host(self):
        """Return the host of this controller."""
        return self.config_entry.data[CONF_HOST]

    @property
    def name(self):
        """Return the controller ID."""
        return self.host

    @property
    def version(self):
        """Return the version."""
        ret = self.api.get_version()
        return ret["version"]

    @property
    def gateway_version(self):
        """Return the version of the gateway."""
        ret = self.api.get_version()
        return ret["gateway"]

    # async def async_update_device_registry(self):
    #     """Update device registry."""
    #     device_registry = await self.hass.helpers.device_registry.async_get_registry()
    #     device_registry.async_get_or_create(
    #         config_entry_id=self.config_entry.entry_id,
    #         identifiers={(DOMAIN, self.bridgeid())},
    #         manufacturer="OpenMotics",
    #         sw_version=self.version(),
    #         gw_verion=self.gateway_version(),
    #     )

    async def async_setup(self):
        """Set up a OpenMotics controller"""
        try:
            self.api = await get_api(
                self.hass,
                self.config_entry.data,
            )

        except CannotConnect:
            raise ConfigEntryNotReady

        except Exception as err:  # pylint: disable=broad-except
            _LOGGER.error("Unknown error connecting with OpenMotics controller: %s", err)
            return False

        return True

    @staticmethod
    async def async_config_entry_updated(hass, entry):
        """Handle signals of config entry being updated.
        This is a static method because a class method (bound method), can not be used with weak references.
        Causes for this is either discovery updating host address or config entry options changing.
        """
        gateway = get_gateway_from_config_entry(hass, entry)
        if not gateway:
            return
        if gateway.api.host != entry.data[CONF_HOST]:
            # TODO
            # gateway.api.close()
            # gateway.api.host = entry.data[CONF_HOST]
            # gateway.api.start()
            return

        # await gateway.options_updated()

    # Returns all the connected devices ###############################################################
    def get_om_output_modules(self):
        """Returns the output_modules."""
        return self.om_output_modules

    def get_scenes(self):
        """Returns the scenes."""
        return self.om_scenes

    def get_om_thermostats_status(self):
        """Returns the thermostats status."""
        return self.om_thermostats_status

    def module_discover_start(self):
        """
        This function gets all the modules connected to this controller and stores in the different platforms.
        """
        # First the modules
        mdls = []
        mdls = self.api.get_modules()
        # Fetching url: https://cloud.openmotics.com/api/get_modules
        # {'outputs': ['O'], 'can_inputs': [], 'success': True, 'shutters': [], 'inputs': ['I']}

        for key, item in mdls.items():
            if key == 'inputs':
                if item is not None:
                    _LOGGER.info("Found input modules.")
                    inputs = []
                    input_configs = self.api.get_input_configurations()
                    # Get the group action configurations.
                    #    result:
                    #    {'success': True, 'timestamp': 1586807416.1240664,
                    #    'config': [{'id': 0, 'name': '', 'actions': ''}, {'id': 1, 'name': '', 'actions': ''},
                    #            {'id': 2, 'name': '', 'actions': ''}, {'id': 3, 'name': '', 'actions': ''},
                    #            {'id': 4, 'name': '', 'actions': ''}, {'id': 5, 'name': '', 'actions': ''},
                    #            {'id': 6, 'name': '', 'actions': ''}, {'id': 7, 'name': '', 'actions': ''},
                    #            ]
                    #    }

                    success = input_configs['success']
                    if success is True:
                        for input_config in input_configs['config']:
                            if (input_config['name'] is None or input_config['name'] == "" or input_config['name'].upper() == NOT_IN_USE):
                                continue
                            inputs.append(input_config)
                    else:
                        _LOGGER.error("Failed to get the input configurations")

                    self.om_input_modules = inputs

            if key == 'outputs':
                if item is not None:
                    _LOGGER.info("Found output modules.")
                    outputs = []
                    output_configs = self.api.get_output_configurations()
                    # Get the output configurations.
                    #    result:
                    #        {'success': True, 'timestamp': 1586803075.5035386,
                    #        'config': [{'id': 0, 'module_type': 'O', 'name': 'Pool', 'timer': 65535, 'floor': 255, 'type': 255, 'can_led_1_id': 255, 'can_led_1_function': 'On B15', 'can_led_2_id': 255, 'can_led_2_function': 'On B15', 'can_led_3_id': 255, 'can_led_3_function': 'On B15', 'can_led_4_id': 255, 'can_led_4_function': 'On B15', 'room': 255},
                    #                    {'id': 1, 'module_type': 'O', 'name': 'Tree', 'timer': 65535, 'floor': 255, 'type': 255, 'can_led_1_id': 255, 'can_led_1_function': 'On B15', 'can_led_2_id': 255, 'can_led_2_function': 'On B15', 'can_led_3_id': 255, 'can_led_3_function': 'On B15', 'can_led_4_id': 255, 'can_led_4_function': 'On B15', 'room': 255},
                    #                    {'id': 2, 'module_type': 'O', 'name': '', 'timer': 65535, 'floor': 255, 'type': 255, 'can_led_1_id': 255, 'can_led_1_function': 'UNKNOWN', 'can_led_2_id': 255, 'can_led_2_function': 'UNKNOWN', 'can_led_3_id': 255, 'can_led_3_function': 'UNKNOWN', 'can_led_4_id': 255, 'can_led_4_function': 'UNKNOWN', 'room': 255},
                    #                    {'id': 3, 'module_type': 'O', 'name': '', 'timer': 65535, 'floor': 255, 'type': 255, 'can_led_1_id': 255, 'can_led_1_function': 'UNKNOWN', 'can_led_2_id': 255, 'can_led_2_function': 'UNKNOWN', 'can_led_3_id': 255, 'can_led_3_function': 'UNKNOWN', 'can_led_4_id': 255, 'can_led_4_function': 'UNKNOWN', 'room': 255},
                    #                    {'id': 4, 'module_type': 'O', 'name': '', 'timer': 65535, 'floor': 255, 'type': 255, 'can_led_1_id': 255, 'can_led_1_function': 'UNKNOWN', 'can_led_2_id': 255, 'can_led_2_function': 'UNKNOWN', 'can_led_3_id': 255, 'can_led_3_function': 'UNKNOWN', 'can_led_4_id': 255, 'can_led_4_function': 'UNKNOWN', 'room': 255},
                    #                    {'id': 5, 'module_type': 'O', 'name': '', 'timer': 65535, 'floor': 255, 'type': 255, 'can_led_1_id': 255, 'can_led_1_function': 'UNKNOWN', 'can_led_2_id': 255, 'can_led_2_function': 'UNKNOWN', 'can_led_3_id': 255, 'can_led_3_function': 'UNKNOWN', 'can_led_4_id': 255, 'can_led_4_function': 'UNKNOWN', 'room': 255},
                    #                    {'id': 6, 'module_type': 'O', 'name': '', 'timer': 65535, 'floor': 255, 'type': 255, 'can_led_1_id': 255, 'can_led_1_function': 'UNKNOWN', 'can_led_2_id': 255, 'can_led_2_function': 'UNKNOWN', 'can_led_3_id': 255, 'can_led_3_function': 'UNKNOWN', 'can_led_4_id': 255, 'can_led_4_function': 'UNKNOWN', 'room': 255},
                    #                    {'id': 7, 'module_type': 'O', 'name': '', 'timer': 65535, 'floor': 255, 'type': 255, 'can_led_1_id': 255, 'can_led_1_function': 'UNKNOWN', 'can_led_2_id': 255, 'can_led_2_function': 'UNKNOWN', 'can_led_3_id': 255, 'can_led_3_function': 'UNKNOWN', 'can_led_4_id': 255, 'can_led_4_function': 'UNKNOWN', 'room': 255}
                    #                    ]
                    #        }

                    success = output_configs['success']
                    if success is True:
                        for output in output_configs['config']:
                            if (output['name'] is None or output['name'] == "" or output['name'].upper() == NOT_IN_USE):
                                continue
                            outputs.append(output)
                    else:
                        _LOGGER.error("Failed to get the output configurations")
                    self.om_output_modules = outputs

            if key == 'success':
                if item is True:
                    _LOGGER.info("Getting modules was successful")

            if key == 'shutters':
                if item is not None:
                    _LOGGER.info("Found shutters modules.")

            if key == 'can_inputs':
                if item is not None:
                    _LOGGER.info("Found can_input modules.")

        # Second the scenes (aka actions)
        actions = []
        actions_configs = self.api.get_group_action_configurations()
        # Get the group action configurations.
        #    result:
        #    {'success': True, 'timestamp': 1586807416.1240664,
        #    'config': [{'id': 0, 'name': 'Lights Tuin On', 'actions': '0,7,0,8'}, {'id': 1, 'name': 'Lights Tuin Off', 'actions': '0,2,0,3'},
        #            {'id': 2, 'name': '', 'actions': ''}, {'id': 3, 'name': '', 'actions': ''},
        #            {'id': 4, 'name': '', 'actions': ''}, {'id': 5, 'name': '', 'actions': ''},
        #            {'id': 6, 'name': '', 'actions': ''}, {'id': 7, 'name': '', 'actions': ''},
        #            ]
        #    }

        success = actions_configs['success']
        if success is True:
            for action in actions_configs['config']:
                if (action['name'] is None or action['name'] == "" or action['name'].upper() == NOT_IN_USE):
                    continue
                actions.append(action)
        else:
            _LOGGER.error("Failed to get the group action configurations")

        self.om_scenes = actions

        return True

    #@Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update the status op the Openmotics modules."""
        with self.mutex:
            if self.last_update_time is None:
                if self.update_status():
                    self.last_update_time = time.time()
                else:
                    # update_status failes, so last_update_time is still None
                    return False

            # Throttle the number of requests to the controller
            if time.time() - self.last_update_time >= MIN_TIME_BETWEEN_UPDATES:
                if self.update_status():
                    self.last_update_time = time.time()
                else:
                    self.last_update_time = None
                    return False

            return True

    def update_status(self):
        """
        Function to force an update of the modules.
        Can be called from within other components and will bypass throttle.
        """

        outputs_status = []
        gos = self.api.get_outputs_status()

        success = gos['success']
        if success is True:
            for status in gos['status']:
                outputs_status.append(status)
        else:
            _LOGGER.error("Failed to get the output statuses")

        self.om_outputs_status = outputs_status

        thermostats_status = []
        gts = self.api.get_thermostats_status()

        success = gts['success']
        if success is True:
            for status in gts['status']:
                thermostats_status.append(status)
        else:
            _LOGGER.error("Failed to get the temperatures statuses")

        self.om_thermostats_status = thermostats_status

        return True

    def get_output_status(self, output_id):
        """
        Function to get the status of a module with id.
        """
        for output_status in self.om_outputs_status:
            if output_status['id'] == output_id:
                return output_status

        _LOGGER.error("No output module found with id: %s", output_id)
        return None


async def get_api(hass, config):
    """Create a gateway and verify authentication."""
    if config[CONF_HOST] == DEFAULT_HOST:
        from .openmoticssdk import OpenMoticsCloudApi
        api = OpenMoticsCloudApi(
            config[CONF_USERNAME],
            config[CONF_PASSWORD],
            )
    else:
        from .openmoticssdk import OpenMoticsApi
        api = OpenMoticsApi(
            config[CONF_USERNAME],
            config[CONF_PASSWORD],
            config[CONF_HOST],
            config[CONF_VERIFY_SSL],
            config[CONF_PORT],
            )
    try:
        with async_timeout.timeout(15):
            await hass.async_add_executor_job(api.get_status)
        return api

    except asyncio.TimeoutError:
        _LOGGER.error(
            "Timeout connecting to the OpenMoticsApi at %s",
            config[CONF_HOST]
            )
        raise CannotConnect

    except AuthenticationException:
        _LOGGER.error(
            "Authentication Exception connecting to the OpenMoticsApi at %s",
            config[CONF_HOST]
            )
        raise AuthenticationRequired

    except MaintenanceModeException:
        _LOGGER.error(
            "OpenMoticsApi at %s is currently in maintenance, please try later.",
            config[CONF_HOST]
            )
        raise CannotConnect

    except ApiException as err:
        _LOGGER.error(err)
        raise CannotConnect
