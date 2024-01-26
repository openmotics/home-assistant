"""Support for OpenMotics thermostat(hroup)s."""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from homeassistant.components.climate import (ATTR_HVAC_MODE, PRESET_AWAY,
                                              ClimateEntity,
                                              ClimateEntityFeature, HVACAction,
                                              HVACMode)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature

from .const import (DOMAIN, NOT_IN_USE, PRESET_AUTO, PRESET_MANUAL,
                    PRESET_PARTY, PRESET_VACATION)
from .entity import OpenMoticsDevice

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import OpenMoticsDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

HVAC_MODES_TO_OM: dict[HVACMode, str] = {
    # HVACMode.HEAT_COOL: "Auto",
    HVACMode.COOL: "COOLING",
    # HVACMode.DRY : "Dry",
    # HVACMode.FAN_ONLY : "Fan",
    HVACMode.HEAT: "HEATING",
    HVACMode.OFF: "OFF",
}
OM_TO_HVAC_MODES = {v: k for k, v in HVAC_MODES_TO_OM.items()}

HVAC_ACTIONS_TO_OM: dict[HVACAction, str] = {
    HVACAction.COOLING: "COOLING",
    HVACAction.HEATING: "HEATING",
}
OM_TO_HVAC_ACTIONS = {v: k for k, v in HVAC_ACTIONS_TO_OM.items()}

PRESET_MODES_TO_OM: dict[str, str] = {
    PRESET_AUTO: "AUTO",
    PRESET_AWAY: "AWAY",
    PRESET_PARTY: "PARTY",
    PRESET_MANUAL: "MANUAL",
    PRESET_VACATION: "VACATION",
}
OM_TO_PRESET_MODES = {v: k for k, v in PRESET_MODES_TO_OM.items()}

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
    tg_entities = []
    tu_entities = []

    coordinator: OpenMoticsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    for tg_index, om_thermostatgroup in enumerate(coordinator.data["thermostatgroups"]):
        tu_entities = []
        for tg_id in om_thermostatgroup.thermostat_ids:
            for tu_index, om_thermostatunit in enumerate(
                coordinator.data["thermostatunits"],
            ):
                # Even if the id is in the list, if the name is not set, don't add it.
                if (
                    om_thermostatunit.name is None
                    or not om_thermostatunit.name
                    or om_thermostatunit.name == NOT_IN_USE
                ):
                    continue

                if tg_id == om_thermostatunit.idx:
                    tu_entities.append(
                        OpenMoticsThermostatUnit(
                            coordinator,
                            tu_index,
                            om_thermostatunit,
                            om_thermostatgroup,
                        ),
                    )
        if tu_entities:
            if om_thermostatgroup.name is None or not om_thermostatgroup.name:
                # If name is empty but there thermostatunits, generate a name
                om_thermostatgroup.name = f"Thermostatgroup-{tg_index}"

            tg_entities.append(
                OpenMoticsThermostatGroup(
                    coordinator,
                    tg_index,
                    om_thermostatgroup,
                ),
            )

    if not tg_entities and not tu_entities:
        _LOGGER.info("No OpenMotics Thermostats added")
        return

    async_add_entities(tg_entities)
    async_add_entities(tu_entities)


class OpenMoticsThermostatGroup(OpenMoticsDevice, ClimateEntity):
    """Representation of a OpenMotics switch."""

    coordinator: OpenMoticsDataUpdateCoordinator

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    # _attr_supported_features = ClimateEntityFeature.HVAC_MODE

    def __init__(
        self,
        coordinator: OpenMoticsDataUpdateCoordinator,
        index: int,
        om_thermostatgroup: dict[str, Any],
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, index, om_thermostatgroup, "climate")

        self._device = self.coordinator.data["thermostatgroups"][self.index]

        self._attr_hvac_modes = [HVACMode.OFF]
        if "HEATING" in om_thermostatgroup.capabilities:
            self._attr_hvac_modes.append(HVACMode.HEAT)
        if "COOLING" in om_thermostatgroup.capabilities:
            self._attr_hvac_modes.append(HVACMode.COOL)

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation ie. heat, cool mode."""
        return OM_TO_HVAC_MODES[self.device.status.mode]


class OpenMoticsThermostatUnit(OpenMoticsDevice, ClimateEntity):
    """Representation of a OpenMotics switch."""

    coordinator: OpenMoticsDataUpdateCoordinator

    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_supported_features = (
        ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TARGET_TEMPERATURE
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
        om_thermostatgroup: dict[str, Any],
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator, index, om_thermostat, "climate")

        self._device = self.coordinator.data["thermostatunits"][self.index]

        self._attr_hvac_modes = [HVACMode.OFF]
        if "HEATING" in om_thermostatgroup.capabilities:
            self._attr_hvac_modes.append(HVACMode.HEAT)
        if "COOLING" in om_thermostatgroup.capabilities:
            self._attr_hvac_modes.append(HVACMode.COOL)

        # Preset modes
        self._attr_preset_modes = list(PRESET_MODES_TO_OM.keys())

    @property
    def hvac_mode(self) -> HVACMode:
        """Return hvac operation ie. heat, cool mode."""
        self._device = self.coordinator.data["thermostatunits"][self.index]
        if self._device.status.state == "OFF":
            return HVACMode.OFF

        # if self.device.status.mode == "HEATING":
        #     return HVACMode.HEAT
        # if self.device.status.mode == "COOLING":
        #     return HVACMode.COOL
        if state := self._device.status.mode:
            return OM_TO_HVAC_MODES[state]

        return HVACMode.OFF

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""
        _LOGGER.debug(
            "Setting thermostat: %s to mode %s",
            self.device_id,
            hvac_mode,
        )
        if hvac_mode == HVACMode.OFF:
            result = await self.coordinator.omclient.thermostats.units.set_state(
                self.device_id,
                "OFF",  # value
            )
        else:
            # heating/cooling is set on Thermostatgroup level, here we can only
            # turn it on/off
            result = await self.coordinator.omclient.thermostats.units.set_state(
                self.device_id,
                "ON",  # value
            )
        await self._update_state_from_result(result, hvac_mode=hvac_mode)

    @property
    def hvac_action(self) -> HVACAction | None:
        """Return the current running hvac operation if supported."""
        try:
            self._device = self.coordinator.data["thermostatunits"][self.index]
            return OM_TO_HVAC_ACTIONS[self._device.status.mode]
        except (AttributeError, KeyError):
            return None

    @property
    def current_temperature(self) -> float:
        """Return current temperature."""
        return self._device.status.current_temperature

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
        await self._update_state_from_result(result, setpoint=temperature)

    @property
    def target_temperature(self) -> float | None:
        """Return the temperature we try to reach."""
        try:
            self._device = self.coordinator.data["thermostatunits"][self.index]
            return self._device.status.current_setpoint
        except (AttributeError, KeyError):
            return None

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set preset mode."""
        # om_preset_mode = PRESET_MODES_TO_OM[preset_mode]
        om_preset_mode = PRESET_MODES_TO_OM[preset_mode]
        _LOGGER.debug(
            "Setting thermostat: %s to preset %s",
            self.device_id,
            om_preset_mode,
        )
        result = await self.coordinator.omclient.thermostats.units.set_preset(
            self.device_id,
            om_preset_mode,
        )
        await self._update_state_from_result(result, om_preset_mode=om_preset_mode)

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode, e.g., home, away, temp."""
        try:
            self._device = self.coordinator.data["thermostatunits"][self.index]
            return OM_TO_PRESET_MODES[self.device.status.active_preset]
        except (AttributeError, KeyError):
            return None

    async def _update_state_from_result(
        self,
        result: Any,
        *,
        setpoint: float | None = None,
        om_preset_mode: str | None = None,
        hvac_mode: str | None = None,
    ) -> None:
        if isinstance(result, dict) and result.get("_error") is None:
            if setpoint is not None:
                self._device.status.current_setpoint = setpoint
            if om_preset_mode is not None:
                self._device.status.active_preset = om_preset_mode
            if hvac_mode is not None:
                if hvac_mode == HVACMode.OFF:
                    self._device.status.state = "OFF"
                else:
                    self._device.status.state = "ON"
                    # self._device.status.mode = PRESET_MODES_INVERTED[preset_mode]
            self.async_write_ha_state()
        else:
            _LOGGER.debug("Invalid result, refreshing all")
            await self.coordinator.async_refresh()
