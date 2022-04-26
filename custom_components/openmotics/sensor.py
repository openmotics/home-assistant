"""Support for HomeAssistant lights."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_TEMPERATURE,
    PERCENTAGE,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, NOT_IN_USE
from .coordinator import OpenMoticsDataUpdateCoordinator
from .entity import OpenMoticsDevice

_LOGGER = logging.getLogger(__name__)

ATTR_HUMIDITY = "humidity"
ATTR_ILLUMINANCE = "illuminance"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Sensors for OpenMotics Controller."""
    entities = []

    coordinator: OpenMoticsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    for index, om_sensor in enumerate(coordinator.data["sensors"]):
        if (
            om_sensor.name is None
            or om_sensor.name == ""
            or om_sensor.name == NOT_IN_USE
        ):
            continue

        if om_sensor.physical_quantity == "temperature":
            entities.append(OpenMoticsTemperature(coordinator, index, om_sensor))

        if om_sensor.physical_quantity == "humidity":
            entities.append(OpenMoticsHumidity(coordinator, index, om_sensor))

        if om_sensor.physical_quantity == "brightness":
            entities.append(OpenMoticsBrightness(coordinator, index, om_sensor))

    if not entities:
        _LOGGER.info("No OpenMotics sensors added")
        return

    async_add_entities(entities)


class OpenMoticsSensor(OpenMoticsDevice, SensorEntity):
    """Representation of a OpenMotics light."""

    coordinator: OpenMoticsDataUpdateCoordinator

    def __init__(
        self,
        coordinator: OpenMoticsDataUpdateCoordinator,
        index,
        device,
    ):
        """Initialize the light."""
        super().__init__(coordinator, index, device, "sensor")

        self._state = None


class OpenMoticsTemperature(OpenMoticsSensor):
    """Representation of a OpenMotics temperature sensor."""

    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _device_class = DEVICE_CLASS_TEMPERATURE

    @property
    def native_value(self):
        """Return % chance the aurora is visible."""
        try:
            self._device = self.coordinator.data["sensors"][self.index]
            return self._device.status.temperature
        except (AttributeError, KeyError):
            return None


class OpenMoticsHumidity(OpenMoticsSensor):
    """Representation of a OpenMotics humidity sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _device_class = DEVICE_CLASS_HUMIDITY

    @property
    def native_value(self):
        """Return % chance the aurora is visible."""
        try:
            self._device = self.coordinator.data["sensors"][self.index]
            return self._device.status.humidity
        except (AttributeError, KeyError):
            return None


class OpenMoticsBrightness(OpenMoticsSensor):
    """Representation of a OpenMotics humidity sensor."""

    _native_unit_of_measurement = PERCENTAGE
    _device_class = DEVICE_CLASS_ILLUMINANCE

    @property
    def native_value(self):
        """Return % chance the aurora is visible."""
        try:
            self._device = self.coordinator.data["sensors"][self.index]
            return self._device.status.brightness
        except (AttributeError, KeyError):
            return None
