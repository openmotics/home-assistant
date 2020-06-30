"""Config flow for OpenMotics integration."""
# from collections import OrderedDict

import voluptuous as vol

# import homeassistant.helpers.config_validation as cv
from homeassistant import core, config_entries
from homeassistant.const import (CONF_CLIENT_ID, CONF_CLIENT_SECRET, CONF_PORT,
                                 CONF_HOST, CONF_VERIFY_SSL)
from homeassistant.core import callback

from .const import (_LOGGER, DEFAULT_HOST, DEFAULT_PORT, DEFAULT_VERIFY_SSL,
                    DOMAIN)
# from .errors import AlreadyConfigured, AuthenticationRequired, CannotConnect
from .errors import CannotConnect, InvalidAuth

from openmotics.clients.cloud import BackendClient, APIError, LegacyClient

# from var_dump import var_dump

DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_HOST, default=DEFAULT_HOST): str,
        vol.Required(CONF_CLIENT_ID): str,
        vol.Required(CONF_CLIENT_SECRET): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): bool,
    }
)

# _LOGGER = logging.getLogger(__name__)

async def validate_input(hass: core.HomeAssistant, data):
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    # ret = []
    # TODO validate the data can be used to set up a connection.

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )
    test = await check_openmotics_connection(hass, data)
    return {"title": data[CONF_HOST]}


async def check_openmotics_connection(hass: core.HomeAssistant, data):
    """
    All functions of OpenMotics return a dictionary, but
    hass.async_add_executor_job has problems when returning
    a dictionary, so this a temporary workaround
    """
    if data[CONF_HOST] == DEFAULT_HOST:
        api = BackendClient(
            data[CONF_CLIENT_ID],
            data[CONF_CLIENT_SECRET]
            )
    else:
        api = BackendClient(
            data[CONF_CLIENT_ID],
            data[CONF_CLIENT_SECRET],
            server=data[CONF_HOST],
            port=data[CONF_PORT],
            ssl=data[CONF_VERIFY_SSL]
            )
    try:
        api.get_token()
    except APIError as err:
        _LOGGER.error(err)
        raise CannotConnect

    return True


@config_entries.HANDLERS.register(DOMAIN)
class OpenMoticsFlowHandler(config_entries.ConfigFlow):
    """Handle a config flow for OpenMotics."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
    """
    def async_get_options_flow(config_entry):
        ""Get the options flow for this handler.""
        return OpenMoticsFlowHandler(config_entry)
    """
    async def async_step_import(self, import_config):
        """Import a config entry from configuration.yaml."""
        # if import_config is None:
        #     _LOGGER.error("Config is None.")
        #     return await self.async_step_user(import_config)

        return self.async_create_entry(
            title=f"{import_config.get(CONF_HOST)} (import from configuration.yaml)",
            data={
                CONF_HOST: import_config.get(CONF_HOST),
                CONF_CLIENT_SECRET: import_config.get(CONF_CLIENT_SECRET),
                CONF_PORT: import_config.get(CONF_PORT),
                CONF_CLIENT_ID: import_config.get(CONF_CLIENT_ID),
                CONF_VERIFY_SSL: import_config.get(CONF_VERIFY_SSL),
            },
        )

    async def async_step_user(self, user_input=None):
        """Handle external yaml configuration."""
        if self._async_current_entries():
            _LOGGER.warning("Only one configuration of OpenMotics is allowed.")
            return self.async_abort(reason="already_setup")

        errors = {}

        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                await self.async_set_unique_id(user_input[CONF_HOST])
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors
        )
