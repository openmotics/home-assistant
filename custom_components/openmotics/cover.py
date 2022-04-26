"""Support for HomeAssistant shutters."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.cover import (  # ATTR_CURRENT_POSITION,; CoverDeviceClass,
    ATTR_POSITION,
    SUPPORT_CLOSE,
    SUPPORT_OPEN,
    SUPPORT_SET_POSITION,
    SUPPORT_STOP,
    CoverEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
    STATE_PAUSED,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, NOT_IN_USE
from .coordinator import OpenMoticsDataUpdateCoordinator
from .entity import OpenMoticsDevice

VALUE_TO_STATE = {
    "DOWN": STATE_CLOSED,
    "GOING_DOWN": STATE_CLOSING,
    "UP": STATE_OPEN,
    "GOING_UP": STATE_OPENING,
    "STOP": STATE_PAUSED,
    None: STATE_UNKNOWN,
}

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up covers for OpenMotics Controller."""
    entities = []

    coordinator: OpenMoticsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    for index, om_cover in enumerate(coordinator.data["shutters"]):
        if om_cover.name is None or om_cover.name == "" or om_cover.name == NOT_IN_USE:
            continue
        entities.append(OpenMoticsShutter(coordinator, index, om_cover))

    if not entities:
        _LOGGER.info("No OpenMotics shutters added")
        return

    async_add_entities(entities)


class OpenMoticsShutter(OpenMoticsDevice, CoverEntity):
    """Representation of a OpenMotics shutter."""

    coordinator: OpenMoticsDataUpdateCoordinator

    def __init__(self, coordinator: OpenMoticsDataUpdateCoordinator, index, device):
        """Initialize the shutter."""
        super().__init__(coordinator, index, device, "cover")

        self._device = self.coordinator.data["shutters"][self.index]
        self._state = None

        self._supported_features = SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP
        if "POSITION" in device.capabilities:
            self._supported_features |= SUPPORT_SET_POSITION

    @property
    def supported_features(self):
        """Flag supported features."""
        return self._supported_features

    @property
    def is_opening(self):
        """Return if the cover is opening or not."""
        try:
            self._device = self.coordinator.data["shutters"][self.index]
            self._state = self._device.status.state
            return VALUE_TO_STATE.get(self._state) == STATE_OPENING
        except (AttributeError, KeyError):
            return STATE_UNKNOWN

    @property
    def is_closing(self):
        """Return if the cover is closing or not."""
        try:
            self._device = self.coordinator.data["shutters"][self.index]
            self._state = self._device.status.state
            return VALUE_TO_STATE.get(self._state) == STATE_CLOSING
        except (AttributeError, KeyError):
            return STATE_UNKNOWN

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        if self.current_cover_position is None:
            return None
        return self.current_cover_position == 0

    @property
    def current_cover_position(self):
        """Return the current position of cover."""
        # for HA None is unknown, 0 is closed, 100 is fully open.
        # for OM 0 is open and 100 is closed
        try:
            self._device = self.coordinator.data["shutters"][self.index]
            if self._device.status.position is None:
                return None
            return 100 - self._device.status.position
        except (AttributeError, KeyError):
            return STATE_UNKNOWN

    async def async_open_cover(self, **kwargs):
        """Open the window cover."""
        await self.coordinator.omclient.shutters.move_up(
            self.device_id,
        )
        await self.coordinator.async_refresh()

    async def async_close_cover(self, **kwargs):
        """Open the window cover."""
        await self.coordinator.omclient.shutters.move_down(
            self.device_id,
        )
        await self.coordinator.async_refresh()

    async def async_stop_cover(self, **kwargs):
        """Stop the window cover."""
        await self.coordinator.omclient.shutters.stop(
            self.device_id,
        )
        await self.coordinator.async_refresh()

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        if not self._supported_features & SUPPORT_SET_POSITION:
            return
        position = 100 - kwargs[ATTR_POSITION]
        await self.coordinator.omclient.shutters.change_position(
            self.device_id,
            position,
        )
        await self.coordinator.async_refresh()
