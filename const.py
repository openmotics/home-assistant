"""Constants for the OpenMotics integration."""
import logging

from datetime import timedelta

_LOGGER = logging.getLogger(__package__)

DOMAIN = "openmotics"
ATTR_MANUFACTURER = "OpenMotics"

DATA_OPENMOTICS_CONFIG = "openmotics_config"
NOT_IN_USE = "NOT_IN_USE"

"""
The state of a light is refreshed every 30 seconds (more or less).
Setting the interval between updates to 30 seconds was just a little bit
to late. 28 seconds is better.
"""
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=28)
# MIN_TIME_BETWEEN_UPDATES = 28  # seconds


DEFAULT_HOST = 'cloud.openmotics.com'
DEFAULT_PORT = 443
DEFAULT_VERIFY_SSL = False


"""
Get a list of all modules attached and registered with the master.
:returns:
    'output': list of module types (O,R,D) and
    'input': list of input module types (I,T,L).
"""
OPENMOTICS_OUTPUT_TYPES = ['O', 'R', 'D']
OPENMOTICS_INPUT_TYPES = ['I', 'T', 'L']

"""
https://wiki.openmotics.com/index.php/Modules
"""
OPENMOTICS_OUTPUT_TYPE_TO_NAME = {
    0: 'outlet',
    1: 'valve',
    2: 'alarm',
    3: 'appliance',
    4: 'pump',
    5: 'hvac',
    6: 'generic',
    7: 'motor',
    8: 'ventilation',
    255: 'light'
}

OPENMOTICS_MODULE_TYPE_TO_NAME = {
    'O': 'Output',
    'R': 'Roller',  # Also known as Shutter
    'D': 'Dimmer',
    'I': 'Input',
    'T': 'Temperature',
    'L': 'Unknown'
}

SUPPORTED_PLATFORMS = ["light", "switch", "scene"]
# SUPPORTED_PLATFORMS = ["light"]
