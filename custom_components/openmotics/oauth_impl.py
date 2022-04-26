"""Local implementation of OAuth2 specific to OpenMotics to
hard code client id and secret and return a proper name."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.config_entry_oauth2_flow import LocalOAuth2Implementation
from pyhaopenmotics.const import CLOUD_SCOPE, OAUTH2_AUTHORIZE, OAUTH2_TOKEN

_LOGGER = logging.getLogger(__name__)


class OpenMoticsOauth2Implementation(LocalOAuth2Implementation):
    """Local implementation of OAuth2 specific to OM to hard code
    client id and secret and return a proper name.
    """

    def __init__(  # pylint: disable=too-many-arguments
        self,
        hass: HomeAssistant,
        domain: str,
        client_id: str,
        client_secret: str,
        name: str,
    ) -> None:
        """Local Toon Oauth Implementation."""
        self._name = name
        """Just init default class with default values."""
        super().__init__(
            hass=hass,
            domain=domain,
            client_id=client_id,
            client_secret=client_secret,
            authorize_url=OAUTH2_AUTHORIZE,
            token_url=OAUTH2_TOKEN,
        )
        _LOGGER.debug("Init OpenMoticsOauth2Implementation: %s", self.name)

    @property
    def name(self) -> str:
        """Name of the implementation."""
        return self._name

    @property
    def extra_authorize_data(self) -> dict[str, str]:
        """Extra data that needs to be appended to the authorize url."""
        return {"scope": " ".join(CLOUD_SCOPE)}

    async def async_resolve_external_data(self, external_data: Any) -> Any:
        """Resolve the authorization code to tokens."""
        # Overruling config_entry_oauth2_flow.
        return await self._token_request(
            {
                "grant_type": "client_credentials",
            }
        )

    async def _async_refresh_token(self, token: dict) -> dict:
        """Refresh tokens."""
        # Overruling config_entry_oauth2_flow.
        _LOGGER.debug("Refreshing token of %s", self.name)
        new_token = await self._token_request(
            {
                "grant_type": "client_credentials",
                # client_id and client_secret is added
                # by _token_request
            }
        )
        return {**token, **new_token}
