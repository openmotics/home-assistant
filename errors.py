"""Errors for the OpenMotics component."""
from homeassistant.exceptions import HomeAssistantError


class OpenMoticsException(HomeAssistantError):
    """Base class for UniFi exceptions."""


class AlreadyConfigured(OpenMoticsException):
    """Controller is already configured."""


class AuthenticationRequired(OpenMoticsException):
    """Unknown error occurred."""


class CannotConnect(OpenMoticsException):
    """Unable to connect to the controller."""


class LoginRequired(OpenMoticsException):
    """Component got logged out."""


class UserLevel(OpenMoticsException):
    """User level too low."""


class InvalidAuth(OpenMoticsException):
    """Authentication failed."""
