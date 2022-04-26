"""Support for HomeAssistant scenes (aka group actions)."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, NOT_IN_USE
from .coordinator import OpenMoticsDataUpdateCoordinator
from .entity import OpenMoticsDevice

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Scenes for OpenMotics Controller."""
    entities = []

    coordinator: OpenMoticsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    for index, om_scene in enumerate(coordinator.data["groupactions"]):
        if om_scene.name is None or om_scene.name == "" or om_scene.name == NOT_IN_USE:
            continue
        entities.append(OpenMoticsScene(coordinator, index, om_scene))

    if not entities:
        _LOGGER.info("No OpenMotics Group Actions (Scenes) added")
        return

    async_add_entities(entities)


class OpenMoticsScene(OpenMoticsDevice, Scene):
    """Representation of a OpenMotics group action."""

    coordinator: OpenMoticsDataUpdateCoordinator

    def __init__(self, coordinator: OpenMoticsDataUpdateCoordinator, index, om_scene):
        """Initialize the scene."""
        super().__init__(coordinator, index, om_scene, "scene")

        self._device = self.coordinator.data["groupactions"][self.index]

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        await self.coordinator.omclient.groupactions.trigger(
            self.device_id,
        )
