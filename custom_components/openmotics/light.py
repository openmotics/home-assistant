"""Support for HomeAssistant lights."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.light import (ATTR_BRIGHTNESS,
                                            COLOR_MODE_BRIGHTNESS,
                                            COLOR_MODE_COLOR_TEMP,
                                            COLOR_MODE_HS, COLOR_MODE_RGBW,
                                            ColorMode, LightEntity)

from .const import DOMAIN, NOT_IN_USE
from .entity import OpenMoticsDevice

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import OpenMoticsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Lights for OpenMotics Controller."""
    entities = []

    coordinator: OpenMoticsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    for index, om_light in enumerate(coordinator.data["outputs"]):
        if om_light.name is None or not om_light.name or om_light.name == NOT_IN_USE:
            continue

        # Outputs can contain outlets and lights, so filter out only the lights
        if om_light.output_type == "LIGHT":
            entities.append(OpenMoticsOutputLight(coordinator, index, om_light))

    for index, om_light in enumerate(coordinator.data["lights"]):
        if om_light.name is None or not om_light.name or om_light.name == NOT_IN_USE:
            continue

        entities.append(OpenMoticsLight(coordinator, index, om_light))

    if not entities:
        _LOGGER.info("No OpenMotics Lights added")
        return

    async_add_entities(entities)


def brightness_to_percentage(byt: int) -> int:
    """Convert brightness from absolute 0..255 to percentage."""
    return min(max(int(round(byt * 100 / 255, 0)), 0), 100)


def brightness_from_percentage(percent: float) -> int:
    """Convert percentage to absolute value 0..255."""
    return min(max(int(round(percent * 255 / 100, 0)), 0), 255)


class OpenMoticsOutputLight(OpenMoticsDevice, LightEntity):
    """Representation of a OpenMotics Output light."""

    coordinator: OpenMoticsDataUpdateCoordinator

    def __init__(
        self,
        coordinator: OpenMoticsDataUpdateCoordinator,
        index: int,
        device: dict[str, Any],
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator, index, device, "light")

        self._attr_supported_color_modes = set()

        if "RANGE" in device.capabilities:
            self._attr_supported_color_modes = {ColorMode.BRIGHTNESS}
            self._attr_color_mode = ColorMode.BRIGHTNESS
        else:
            self._attr_supported_color_modes = {ColorMode.ONOFF}
            self._attr_color_mode = ColorMode.ONOFF

    @property
    def is_on(self) -> Any:
        """Return true if device is on."""
        try:
            self._device = self.coordinator.data["outputs"][self.index]
            return self._device.status.on
        except (AttributeError, KeyError):
            return None

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        try:
            self._device = self.coordinator.data["outputs"][self.index]
            return brightness_from_percentage(self._device.status.value)
        except (AttributeError, KeyError):
            return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn device on."""
        # brightness = kwargs.get(ATTR_BRIGHTNESS)
        # if brightness is not None:
        _LOGGER.debug(
            "kwargs: %s",
            kwargs,
        )
        if (
            brightness := kwargs.get(ATTR_BRIGHTNESS)
        ) is not None:
            # Openmotics brightness (value) is between 0..100
            _LOGGER.debug(
                "Turning on light: %s brightness %s",
                self.device_id,
                brightness,
            )
            result = await self.coordinator.omclient.outputs.turn_on(
                self.device_id,
                brightness_to_percentage(brightness),  # value
            )
        else:
            _LOGGER.debug("Turning on light: %s", self.device_id)
            result = await self.coordinator.omclient.outputs.turn_on(
                self.device_id,
            )

        await self._update_state_from_result(result, True, brightness)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn device off."""
        _LOGGER.debug("Turning off light: %s", self.device_id)
        result = await self.coordinator.omclient.outputs.turn_off(
            self.device_id,
        )
        await self._update_state_from_result(result, False, None)

    async def _update_state_from_result(
        self,
        result: Any,
        state: bool,
        brightness: int | None,
    ) -> None:
        if isinstance(result, dict) and result.get("_error") is None:
            self._device.status.on = state
            if brightness is not None:
                self._device.status.value = brightness
            self.async_write_ha_state()
        else:
            _LOGGER.debug("Invalid result, refreshing all")
            await self.coordinator.async_refresh()


class OpenMoticsLight(OpenMoticsDevice, LightEntity):
    """Representation of a OpenMotics light."""

    coordinator: OpenMoticsDataUpdateCoordinator

    def __init__(
        self,
        coordinator: OpenMoticsDataUpdateCoordinator,
        index: int,
        device: dict[str, Any],
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator, index, device, "light")

        self._attr_supported_color_modes = set()

        if "RANGE" in device.capabilities:
            self._attr_supported_color_modes.add(COLOR_MODE_BRIGHTNESS)
            # Default: Brightness (no color)
            self._attr_color_mode = COLOR_MODE_BRIGHTNESS

        if "WHITE_TEMP" in device.capabilities:
            self._attr_supported_color_modes.add(COLOR_MODE_COLOR_TEMP)
            self._attr_supported_color_modes.add(COLOR_MODE_HS)

        if "FULL_COLOR" in device.capabilities:
            self._attr_supported_color_modes.add(COLOR_MODE_RGBW)

    @property
    def is_on(self) -> Any:
        """Return true if device is on."""
        try:
            self._device = self.coordinator.data["lights"][self.index]
            return self._device.status.on
        except (AttributeError, KeyError):
            return None

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        try:
            self._device = self.coordinator.data["lights"][self.index]
            return brightness_from_percentage(self._device.status.value)
        except (AttributeError, KeyError):
            return None

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn device on."""
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness is not None:
            # Openmotics brightness (value) is between 0..100
            _LOGGER.debug(
                "Turning on light: %s brightness %s",
                self.device_id,
                brightness,
            )
            result = await self.coordinator.omclient.lights.turn_on(
                self.device_id,
                brightness_to_percentage(brightness),  # value
            )
        else:
            _LOGGER.debug("Turning on light: %s", self.device_id)
            result = await self.coordinator.omclient.lights.turn_on(
                self.device_id,
            )

        await self._update_state_from_result(result, True, brightness)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn device off."""
        _LOGGER.debug("Turning off light: %s", self.device_id)
        result = await self.coordinator.omclient.lights.turn_off(
            self.device_id,
        )
        await self._update_state_from_result(result, False, None)

    async def _update_state_from_result(
        self,
        result: Any,
        state: bool,
        brightness: int | None,
    ) -> None:
        if isinstance(result, dict) and result.get("_error") is None:
            self._device.status.on = state
            if brightness is not None:
                self._device.status.value = brightness
            self.async_write_ha_state()
        else:
            _LOGGER.debug("Invalid result, refreshing all")
            await self.coordinator.async_refresh()
