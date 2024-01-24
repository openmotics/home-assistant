"""Support for OpenMotics thermostat(hroup)s."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.climate import (ATTR_HVAC_MODE, PRESET_ACTIVITY,
                                              PRESET_AWAY, PRESET_ECO,
                                              PRESET_HOME, ClimateEntity,
                                              ClimateEntityFeature, HVACAction,
                                              HVACMode)
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

HVAC_MODES: dict[str, HVACMode] = {
    # "auto": HVACMode.HEAT_COOL,
    "COOLING": HVACMode.COOL,
    # "dry": HVACMode.DRY,
    # "fan": HVACMode.FAN_ONLY,
    "HEATING": HVACMode.HEAT,
    "OFF": HVACMode.OFF,
}
HVAC_MODES_INVERTED = {v: k for k, v in HVAC_MODES.items()}

HVAC_ACTIONS: dict[str, HVACAction] = {
    "COOLING": HVACAction.COOLING,
    "HEATING": HVACAction.HEATING,
}
HVAC_ACTIONS_INVERTED = {v: k for k, v in HVAC_ACTIONS.items()}

PRESET_MODES: dict[str, str] = {
    "AUTO": PRESET_HOME,
    "AWAY": PRESET_AWAY,
    "PARTY": PRESET_ACTIVITY,
    "VACATION": PRESET_ECO,
}
PRESET_MODES_INVERTED = {v: k for k, v in PRESET_MODES.items()}

# MAP_STATE_ICONS = {
#     HVACMode.COOL: "mdi:snowflake",
#     HVACMode.DRY: "mdi:water-off",
#     HVACMode.FAN_ONLY: "mdi:fan",
#     HVACMode.HEAT: "mdi:white-balance-sunny",
#     HVACMode.HEAT_COOL: "mdi:cached",
# }

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
        # ClimateEntityFeature.TARGET_TEMPERATURE
    )

    # OpenMotics thermostats go from 6 to 32 degress
    _attr_min_temp = 6.0
    _attr_max_temp = 32.0


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

        # Preset modes
        self._attr_preset_modes = list(PRESET_MODES.keys())


    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation ie. heat, cool mode."""
        if self.device.status.state == "OFF":
            return HVACMode.OFF

        # if self.device.status.mode == "HEATING":
        #     return HVACMode.HEAT
        # if self.device.status.mode == "COOLING":
        #     return HVACMode.COOL
        if (
            state := self.device.status.mode
        ) and state.value_as_str:
            return HVAC_MODES[state.value_as_str]

        return HVACMode.OFF

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        _LOGGER.debug(
                "Setting thermostat: %s to mode %s",
                self.device_id,
                hvac_mode,
            )
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
        if hvac_mode == HVACMode.HEAT:
            if self.hvac_mode == HVACMode.OFF:
                await self.coordinator.omclient.thermostats.units.set_state(
                    self.device_id,
                    "ON",  # value
                )
            await self.coordinator.omclient.thermostats.groups.set_mode(
                self.device_id,
                HVAC_MODES_INVERTED[hvac_mode],
             )
            return

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation if supported."""
        if (
            current_action := self.device.status.mode
        ) and current_action.value_as_str:
            return HVAC_ACTIONS[current_action.value_as_str]

        return None

    @property
    def current_temperature(self) -> int | None:
        """Return current temperature."""
        return self.device.status.current_temperature

        return None

    async def async_set_temperature(self, **kwargs: Any) -> None:
        """Set new target temperature."""
        if hvac_mode := kwargs.get(ATTR_HVAC_MODE):
            await self.async_set_hvac_mode(hvac_mode)

        if (temperature := kwargs.get(ATTR_TEMPERATURE)) is None:
            return
        _LOGGER.debug(
                "Setting thermostat: %s to temperature %s",
                self.device_id,
                temperature,
            )
        result = await self.coordinator.omclient.thermostats.units.set_temperature(
            self.device_id,
            temperature,  # value
        )
        await self._update_state_from_result(result, temperature=temperature)

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        return self.device.status.setpoint


    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode."""
        om_preset_mode = PRESET_MODES_INVERTED[preset_mode]
        result = await self.coordinator.omclient.thermostats.units.set_preset(
            self.device_id,
            om_preset_mode,  # value
        )
        await self._update_state_from_result(result, preset_mode=om_preset_mode)


    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode, e.g., home, away, temp."""
        if (
            om_preset_mode := self.device.status.preset
        ) and om_preset_mode.value_as_str:
            return PRESET_MODES[om_preset_mode.value_as_str]
        return None


    # if isinstance(result, dict) and result.get("_error") is None:
    #      if temperature is not None:
    #         self._device.status.position = position
    #     self.async_write_ha_state()
    # else:
    #     _LOGGER.debug("Invalid result, refreshing all")
    #     await self.coordinator.async_refresh()


    async def _update_state_from_result(
        self,
        result: Any,
        *,
        temperature: float | None = None,
        preset_mode: str | None = None,
        other: int | None = None,
    ) -> None:
        pass
