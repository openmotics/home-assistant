"""The Openmotics integration.

    Support for OpenMotics.
    For more details about this component, please refer to the documentation at
    https://github.com/openmotics/home-assistant

    For examples of the output of the api, look at openmotics_api.md
"""
# pylint: disable=import-outside-toplevel
import asyncio

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import \
    SOURCE_IMPORT  # Needed for config_flow
from homeassistant.const import (CONF_HOST, CONF_PASSWORD, CONF_PORT,
                                 CONF_USERNAME, CONF_VERIFY_SSL)

from .const import (_LOGGER, DATA_OPENMOTICS_CONFIG, DEFAULT_HOST,
                    DEFAULT_PORT, DEFAULT_VERIFY_SSL, DOMAIN,
                    SUPPORTED_PLATFORMS)
from .gateway import OpenMoticsGateway

# from var_dump import var_dump


from .errors import AlreadyConfigured, AuthenticationRequired, CannotConnect
from .openmoticssdk import (ApiException, AuthenticationException,
                           MaintenanceModeException, traceback)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({
        vol.Optional(CONF_USERNAME, 'auth'): cv.string,
        vol.Optional(CONF_PASSWORD, 'auth'): cv.string,
        vol.Optional(CONF_HOST, default=DEFAULT_HOST):
            # vol.All(cv.string, is_socket_address),
            cv.string,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
        vol.Optional(CONF_VERIFY_SSL,
                     default=DEFAULT_VERIFY_SSL): cv.boolean,
    })},
    extra=vol.ALLOW_EXTRA
    )


async def async_setup(hass, config):
    """
    Openmotics uses config flow for configuration.

    But, an "openmotics:" entry in configuration.yaml will trigger an import
    flow if a config entry doesn't already exist.
    """
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    hass.data[DATA_OPENMOTICS_CONFIG] = conf

    if hass.config_entries.async_entries(DOMAIN):
        _LOGGER.debug("Config entries exists.")

    if not hass.config_entries.async_entries(DOMAIN) and hass.data[DATA_OPENMOTICS_CONFIG]:
        # No config entry exists and configuration.yaml config exists, trigger the import flow.
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data={
                    CONF_HOST: conf.get(CONF_HOST, DEFAULT_HOST),
                    CONF_USERNAME: conf.get(CONF_USERNAME),
                    CONF_PASSWORD: conf.get(CONF_PASSWORD),
                    CONF_PORT: conf.get(CONF_PORT, DEFAULT_PORT),
                    CONF_VERIFY_SSL: conf.get(CONF_VERIFY_SSL, DEFAULT_VERIFY_SSL),
                },
            )
        )

    return True


async def async_setup_entry(hass, config_entry):
    """Set up OpenMotics Gateway from a config entry."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    # hass.data[OM_CTRL] = OpenMoticsGateway(hass, config_entry)
    # gateway = hass.data[OM_CTRL]
    gateway = OpenMoticsGateway(hass, config_entry)
    _LOGGER.debug("before async_setup")
    try:
        if not await gateway.async_setup():
            return False

        status = gateway.api.get_status()

    except AuthenticationException as err:
        _LOGGER.error(err)
        raise InvalidAuth

    except (MaintenanceModeException, ApiException) as err:
        _LOGGER.error(err)
        raise CannotConnect

    except Exception as err:
        # traceback.print_exc()
        raise CannotConnect

    if status['success'] is False:
        _LOGGER.debug("Something went wrong initialising the gateway")
        return False

    hass.data[DOMAIN][config_entry.unique_id] = gateway

    gateway.module_discover_start()

    gateway.update()

    for platform in SUPPORTED_PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(
                config_entry,
                platform
                )
        )

    return True


async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(
                    config_entry,
                    platform
                    )
                for platform in SUPPORTED_PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(config_entry)
        hass.data.pop(DOMAIN)

    return unload_ok
