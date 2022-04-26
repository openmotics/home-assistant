"""Generic OpenMoticDevice Entity."""
from __future__ import annotations

from typing import Any

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OpenMoticsDataUpdateCoordinator


class OpenMoticsDevice(CoordinatorEntity):
    """Representation a base OpenMotics device."""

    coordinator: OpenMoticsDataUpdateCoordinator

    def __init__(
        self,
        coordinator: OpenMoticsDataUpdateCoordinator,
        index: str,
        device,
        device_type: str,
    ) -> None:
        """Initialize the device."""
        super().__init__(coordinator=coordinator)

        self.omclient = coordinator.omclient
        self._install_id = coordinator.install_id
        self._index = index
        self._device = device

        self._local_id = device.local_id
        self._idx = device.idx
        self._type = device_type

        # inherited properties
        self._attr_name = device.name
        self._attr_available = True
        # Because polling is so common, Home Assistant by default assumes
        # that your entity is based on polling.
        self._attr_should_poll = False

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            name=self.name,
            model=self._type,
            id=self._idx,
            installation=self._install_id,
            manufacturer="OpenMotics",
        )

    @property
    def device(self) -> Any:
        """Return the device."""
        return self._device

    @property
    def floor(self) -> Any:
        """Return the floor of the device."""
        try:
            location = self._device["location"]
            return location["floor_id"]
        except (AttributeError, KeyError):
            return "N/A"

    @property
    def room(self) -> Any:
        """Return the room of the device."""
        try:
            location = self._device["location"]
            return location["room_id"]
        except (AttributeError, KeyError):
            return "N/A"

    @property
    def index(self) -> Any:
        """Return the index."""
        return self._index

    @property
    def unique_id(self) -> Any:
        """Return a unique ID."""
        return f"{self.install_id}-{self.device_id}"

    @property
    def device_id(self) -> Any:
        """Return a unique ID."""
        return self._idx

    @property
    def type(self) -> Any:
        """Return a unique ID."""
        return self._type

    @property
    def install_id(self):
        """Return the installation ID."""
        return self._install_id
