"""Support for HomeAssistant lights."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
)

from .const import DOMAIN, NOT_IN_USE
from .entity import OpenMoticsDevice

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import OpenMoticsDataUpdateCoordinator


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
        if om_sensor.name is None or not om_sensor.name or om_sensor.name == NOT_IN_USE:
            continue

        if om_sensor.physical_quantity == "temperature":
            entities.append(OpenMoticsTemperature(coordinator, index, om_sensor))

        if om_sensor.physical_quantity == "humidity":
            entities.append(OpenMoticsHumidity(coordinator, index, om_sensor))

        if om_sensor.physical_quantity == "brightness":
            entities.append(OpenMoticsBrightness(coordinator, index, om_sensor))

    for index, om_sensor in enumerate(coordinator.data["energysensors"]):
        if om_sensor.name is None or not om_sensor.name or om_sensor.name == NOT_IN_USE:
            continue

        entities.append(OpenMoticsVoltage(coordinator, index, om_sensor))
        entities.append(OpenMoticsFrequency(coordinator, index, om_sensor))
        entities.append(OpenMoticsCurrent(coordinator, index, om_sensor))
        entities.append(OpenMoticsPower(coordinator, index, om_sensor))

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
        index: int,
        device: dict[str, Any],
    ) -> None:
        """Initialize the light."""
        super().__init__(coordinator, index, device, "sensor")

        self._state = None


class OpenMoticsTemperature(OpenMoticsSensor):
    """Representation of a OpenMotics temperature sensor."""

    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    @property
    def native_value(self) -> float | None:
        """Return % chance the aurora is visible."""
        try:
            self._device = self.coordinator.data["sensors"][self.index]
            return self._device.status.temperature
        except (AttributeError, KeyError):
            return None


class OpenMoticsHumidity(OpenMoticsSensor):
    """Representation of a OpenMotics humidity sensor."""

    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> float | None:
        """Return % chance the aurora is visible."""
        try:
            self._device = self.coordinator.data["sensors"][self.index]
            return self._device.status.humidity
        except (AttributeError, KeyError):
            return None


class OpenMoticsBrightness(OpenMoticsSensor):
    """Representation of a OpenMotics humidity sensor."""

    _attr_device_class = SensorDeviceClass.ILLUMINANCE
    # _attr_native_unit_of_measurement = LIGHT_LUX
    # TODO: convert percentage to flux
    _attr_native_unit_of_measurement = PERCENTAGE

    @property
    def native_value(self) -> float | None:
        """Return % chance the aurora is visible."""
        try:
            self._device = self.coordinator.data["sensors"][self.index]
            return self._device.status.brightness
        except (AttributeError, KeyError):
            return None


class OpenMoticsEnergySensor(OpenMoticsSensor):
    """Representation of a OpenMotics energy sensor."""

    @dataclass
    class WrappedDevice:
        """Representation of a OpenMotics energy sensor."""

        idx: int
        local_id: int
        name: str
        device: dict[str, Any]

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_device_class: SensorDeviceClass

    def __init__(
        self,
        coordinator: OpenMoticsDataUpdateCoordinator,
        index: int,
        device: dict[str, Any],
    ) -> None:
        """Representation of a OpenMotics energy sensor."""
        self._energy_index = index
        super().__init__(
            coordinator,
            index,
            OpenMoticsEnergySensor.WrappedDevice(
                f"energy-{device.idx}-{self.device_class}",
                device.idx,
                device.name,
                device,
            ),
        )


class OpenMoticsVoltage(OpenMoticsEnergySensor):
    """Representation of a OpenMotics voltage sensor."""

    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_icon = "mdi:flash-outline"

    @property
    def native_value(self) -> float | None:
        """Return % chance the aurora is visible."""
        try:
            self._device = self.coordinator.data["energysensors"][self.index]
            return self._device.status.voltage
        except (AttributeError, KeyError):
            return None


class OpenMoticsFrequency(OpenMoticsEnergySensor):
    """Representation of a OpenMotics frequency sensor."""

    _attr_native_unit_of_measurement = UnitOfFrequency.HERTZ
    _attr_device_class = SensorDeviceClass.FREQUENCY
    _attr_icon = "mdi:sine-wave"

    @property
    def native_value(self) -> float | None:
        """Return % chance the aurora is visible."""
        try:
            self._device = self.coordinator.data["energysensors"][self.index]
            return self._device.status.frequency
        except (AttributeError, KeyError):
            return None


class OpenMoticsCurrent(OpenMoticsEnergySensor):
    """Representation of a OpenMotics current sensor."""

    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_device_class: SensorDeviceClass = SensorDeviceClass.CURRENT
    _attr_icon = "mdi:current-ac"

    @property
    def native_value(self) -> float | None:
        """Return % chance the aurora is visible."""
        try:
            self._device = self.coordinator.data["energysensors"][self.index]
            return self._device.status.current
        except (AttributeError, KeyError):
            return None


class OpenMoticsPower(OpenMoticsEnergySensor):
    """Representation of a OpenMotics power sensor."""

    _attr_device_class = SensorDeviceClass.POWER
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_icon = "mdi:flash-outline"

    @property
    def native_value(self) -> float | None:
        """Return % chance the aurora is visible."""
        try:
            self._device = self.coordinator.data["energysensors"][self.index]
            return self._device.status.power
        except (AttributeError, KeyError):
            return None
