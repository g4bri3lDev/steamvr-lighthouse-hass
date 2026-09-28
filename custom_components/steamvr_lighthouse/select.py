"""Power mode and channel selects for SteamVR Lighthouse base stations."""

from functools import partial

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from lighthouse_ble import PowerState
from lighthouse_ble.const import CHANNEL_MAX, CHANNEL_MIN

from .coordinator import LighthouseConfigEntry
from .entity import LighthouseEntity

PARALLEL_UPDATES = 0

POWER_MODE = SelectEntityDescription(key="power_mode", translation_key="power_mode")
CHANNEL = SelectEntityDescription(
    key="channel",
    translation_key="channel",
    entity_category=EntityCategory.CONFIG,
    options=[str(channel) for channel in range(CHANNEL_MIN, CHANNEL_MAX + 1)],
)

_MODE_FOR_STATE = {
    PowerState.ON: "on",
    PowerState.BOOTING: "on",
    PowerState.STANDBY: "standby",
    PowerState.SLEEP: "sleep",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LighthouseConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the selects."""
    coordinator = entry.runtime_data
    async_add_entities(
        [
            LighthousePowerModeSelect(coordinator, POWER_MODE),
            LighthouseChannelSelect(coordinator, CHANNEL),
        ]
    )


class LighthousePowerModeSelect(LighthouseEntity, SelectEntity):
    """Choose between on, standby and sleep."""

    @property
    def options(self) -> list[str]:
        """Return the modes this station's firmware supports."""
        if self.coordinator.station.supports_standby is False:
            return ["on", "sleep"]
        return ["on", "standby", "sleep"]

    @property
    def current_option(self) -> str | None:
        """Return the mode the station is in or heading to."""
        power = self.station_state.power
        return _MODE_FOR_STATE.get(power) if power is not None else None

    async def async_select_option(self, option: str) -> None:
        """Switch the station to the chosen mode."""
        station = self.coordinator.station
        await self.coordinator.async_run_command(
            partial(station.set_power, PowerState(option))
        )


class LighthouseChannelSelect(LighthouseEntity, SelectEntity):
    """The station's tracking channel."""

    @property
    def current_option(self) -> str | None:
        """Return the current channel."""
        channel = self.station_state.channel
        return str(channel) if channel is not None else None

    async def async_select_option(self, option: str) -> None:
        """Move the station to another channel."""
        station = self.coordinator.station
        await self.coordinator.async_run_command(
            partial(station.set_channel, int(option))
        )
