"""Support for OpenMotics thermostat(hroup)s."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.climate import (ClimateEntity,
                                              ClimateEntityFeature, HVACMode)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

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

    for gindex, om_thermostatgroup in enumerate(coordinator.data["thermostatgroups"]):
        for tg_id in om_thermostatgroup.thermostat_ids:
            for index, om_thermostat in enumerate(coordinator.data["thermostatunits"]):
                # Even if the id is in the list, if the name is not set, don't add it.
                if (
                    om_thermostat.name is None
                    or not om_thermostat.name
                    or om_thermostat.name == NOT_IN_USE
                ):
                    continue

                if tg_id == om_thermostat.idx:
                    entities.append(
                        OpenMoticsClimate(
                            coordinator,
                            index,
                            om_thermostat,
                            gindex,
                            om_thermostatgroup,
                        ),
                    )

    if not entities:
        _LOGGER.info("No OpenMotics Thermostats added")
        return

    async_add_entities(entities)


class OpenMoticsClimate(OpenMoticsDevice, ClimateEntity):
    """Representation of a OpenMotics switch."""

    coordinator: OpenMoticsDataUpdateCoordinator

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.PRESET_MODE | ClimateEntityFeature.TARGET_TEMPERATURE
    )

    # Both min and max temp values have been retrieved from the Somfy Application.
    _attr_min_temp = 15.0
    _attr_max_temp = 26.0


    def __init__(
        self,
        coordinator: OpenMoticsDataUpdateCoordinator,
        index: int,
        om_thermostat: dict[str, Any],
        gindex: int,
        om_thermostatgroup: dict[str, Any],
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, index, om_thermostat, "climate")

        self._device = self.coordinator.data["thermostatunits"][self.index]

        self.group_index = gindex

        self._attr_hvac_modes = [HVACMode.OFF]
        if "HEATING" in om_thermostatgroup.capabilities:
            self._attr_hvac_modes.append(HVACMode.HEAT)
        if "COOLING" in om_thermostatgroup.capabilities:
            self._attr_hvac_modes.append(HVACMode.COOL)

    @property
    def hvac_mode(self) -> HVACMode | None:
        """Return hvac operation ie. heat, cool mode."""
        if self.device.status.state == "OFF":
            return HVACMode.OFF
        if self.device.status.mode == "HEATING":
            return HVACMode.HEAT
        if self.device.status.mode == "COOLING":
            return HVACMode.COOL
        return None

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        # if hvac_mode == HVACMode.ON:
        #     await self.coordinator.omclient.thermostats.units.set_state(
        #         self.device_id,
        #         "ON",  # value
        #     )
        #     return
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.omclient.thermostats.units.set_state(
                self.device_id,
                "OFF",  # value
            )
            return

    @property
    def current_temperature(self) -> int | None:
        """Return current temperature."""
        return self.device.status.current_temperature

        return None

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        result = await self.coordinator.omclient.thermostats.units.set_temperature(
            self.device_id,
            temperature,  # value
        )
        await self._update_state_from_result(result, temperature=temperature)

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self.device.status.setpoint

    async def _update_state_from_result(
        self,
        result: Any,
        *,
        temperature: float | None = None,
        other: int | None = None,
    ) -> None:
        pass

    # @property
    # def preset_mode(self) -> str:
    #     """Return the current preset mode, e.g., home, away, temp."""
    #     if self.device.status.preset == "AUTO":
    #         return HVACMode.AUTO
    #     if self.device.status.preset == "AWAY":
    #         return PRESET_AWAY
    #     if self.device.status.preset == "PARTY":
    #         return HVACMode.AUTO
    #     if self.device.status.preset == "VACATION":
    #         return HVACMode.AUTO




    # if isinstance(result, dict) and result.get("_error") is None:
    #      if temperature is not None:
    #         self._device.status.position = position
    #     self.async_write_ha_state()
    # else:
    #     _LOGGER.debug("Invalid result, refreshing all")
    #     await self.coordinator.async_refresh()
