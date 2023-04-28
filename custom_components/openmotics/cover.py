"""Support for HomeAssistant shutters."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.const import (
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_OPEN,
    STATE_OPENING,
    STATE_PAUSED,
    STATE_UNKNOWN,
)

from .const import DOMAIN, NOT_IN_USE
from .entity import OpenMoticsDevice

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import OpenMoticsDataUpdateCoordinator


VALUE_TO_STATE = {
    "DOWN": STATE_CLOSED,
    "GOING_DOWN": STATE_CLOSING,
    "UP": STATE_OPEN,
    "GOING_UP": STATE_OPENING,
    "STOPPED": STATE_PAUSED,
    None: STATE_UNKNOWN,
}
STATE_TO_VALUE = {v: k for k, v in VALUE_TO_STATE.items()}

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
        if om_cover.name is None or not om_cover.name or om_cover.name == NOT_IN_USE:
            continue
        entities.append(OpenMoticsShutter(coordinator, index, om_cover))

    if not entities:
        _LOGGER.info("No OpenMotics shutters added")
        return

    async_add_entities(entities)


class OpenMoticsShutter(OpenMoticsDevice, CoverEntity):
    """Representation of a OpenMotics shutter."""

    coordinator: OpenMoticsDataUpdateCoordinator

    def __init__(
        self,
        coordinator: OpenMoticsDataUpdateCoordinator,
        index: int,
        device: dict[str, Any],
    ) -> None:
        """Initialize the shutter."""
        super().__init__(coordinator, index, device, "cover")

        self._device = self.coordinator.data["shutters"][self.index]
        self._state = None

        self._supported_features = CoverEntityFeature.OPEN
        self._supported_features |= CoverEntityFeature.CLOSE
        self._supported_features |= CoverEntityFeature.STOP

        if "POSITION" in device.capabilities:
            self._supported_features |= CoverEntityFeature.SET_POSITION

    @property
    def supported_features(self) -> CoverEntityFeature:
        """Flag supported features."""
        return self._supported_features

    @property
    def is_opening(self) -> bool:
        """Return if the cover is opening or not."""
        try:
            self._device = self.coordinator.data["shutters"][self.index]
            self._state = self._device.status.state.upper()
            return VALUE_TO_STATE.get(self._state) == STATE_OPENING
        except (AttributeError, KeyError):
            return STATE_UNKNOWN

    @property
    def is_closing(self) -> bool:
        """Return if the cover is closing or not."""
        try:
            self._device = self.coordinator.data["shutters"][self.index]
            self._state = self._device.status.state.upper()
            return VALUE_TO_STATE.get(self._state) == STATE_CLOSING
        except (AttributeError, KeyError):
            return STATE_UNKNOWN

    @property
    def is_closed(self) -> bool:
        """Return if the cover is closed."""
        if self.current_cover_position is None:
            return None
        return self.current_cover_position == 0

    @property
    def current_cover_position(self) -> int | None:
        """Return the current position of cover."""
        # for HA None is unknown, 0 is closed, 100 is fully open.
        # for OM 0 is open and 100 is closed
        try:
            self._device = self.coordinator.data["shutters"][self.index]
            if self._supported_features & CoverEntityFeature.SET_POSITION:
                if self._device.status.position is None:
                    return None
                return 100 - self._device.status.position

            if VALUE_TO_STATE.get(self._state) == STATE_CLOSED:
                return 0
            if VALUE_TO_STATE.get(self._state) == STATE_OPEN:
                return 100
            if VALUE_TO_STATE.get(self._state) == STATE_PAUSED:
                # status":{"state":"STOPPED","position":100,"locked":false,"last_change":1682703027.962422}
                if self._device.status.position is None:
                    return None
                return 100 - self._device.status.position

            return STATE_UNKNOWN
        except (AttributeError, KeyError):
            return STATE_UNKNOWN

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Open the window cover."""
        result = await self.coordinator.omclient.shutters.move_up(
            self.device_id,
        )
        await self._update_state_from_result(result, state=STATE_OPENING)

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Open the window cover."""
        result = await self.coordinator.omclient.shutters.move_down(
            self.device_id,
        )
        await self._update_state_from_result(result, state=STATE_CLOSING)

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the window cover."""
        result = await self.coordinator.omclient.shutters.stop(
            self.device_id,
        )
        await self._update_state_from_result(result, state=STATE_PAUSED)

    async def async_set_cover_position(self, **kwargs: Any) -> None:
        """Move the cover to a specific position."""
        if not self._supported_features & CoverEntityFeature.SET_POSITION:
            return
        position = 100 - kwargs[ATTR_POSITION]
        result = await self.coordinator.omclient.shutters.change_position(
            self.device_id,
            position,
        )
        await self._update_state_from_result(result, position=position)

    async def _update_state_from_result(
        self,
        result: Any,
        *,
        state: str | None = None,
        position: int | None = None,
    ) -> None:
        if isinstance(result, dict) and result.get("_error") is None:
            if state is not None:
                self._state = STATE_TO_VALUE.get(state)
                self._device.status.state = self._state
            if position is not None:
                self._device.status.position = position
            self.async_write_ha_state()
        else:
            _LOGGER.debug("Invalid result, refreshing all")
            await self.coordinator.async_refresh()
