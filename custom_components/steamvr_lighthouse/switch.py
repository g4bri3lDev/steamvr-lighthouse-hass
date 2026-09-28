"""Power switch for SteamVR Lighthouse base stations."""

from functools import partial
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from lighthouse_ble import PowerState, UnsupportedError

from .const import CONF_OFF_ACTION, DEFAULT_OFF_ACTION, OffAction
from .coordinator import LighthouseConfigEntry
from .entity import LighthouseEntity

PARALLEL_UPDATES = 0

POWER = SwitchEntityDescription(key="power", translation_key="power")


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LighthouseConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the power switch."""
    async_add_entities([LighthousePowerSwitch(entry.runtime_data, POWER)])


class LighthousePowerSwitch(LighthouseEntity, SwitchEntity):
    """Turns the station on, or to sleep/standby depending on the options."""

    @property
    def is_on(self) -> bool | None:
        """Return True while the station is on or on its way there."""
        power = self.station_state.power
        if power is None or power is PowerState.UNKNOWN:
            return None
        return power in (PowerState.ON, PowerState.BOOTING)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Wake the station."""
        station = self.coordinator.station
        await self.coordinator.async_run_command(
            partial(station.set_power, PowerState.ON)
        )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Put the station to sleep or in standby."""
        station = self.coordinator.station
        off_action = self.coordinator.entry.options.get(
            CONF_OFF_ACTION, DEFAULT_OFF_ACTION
        )
        if off_action != OffAction.STANDBY or station.supports_standby is False:
            await self.coordinator.async_run_command(
                partial(station.set_power, PowerState.SLEEP)
            )
            return

        async def standby_or_sleep() -> None:
            try:
                await station.set_power(PowerState.STANDBY)
            except UnsupportedError:
                # Firmware without standby is only detected once a command connects.
                await station.set_power(PowerState.SLEEP)

        await self.coordinator.async_run_command(standby_or_sleep)
