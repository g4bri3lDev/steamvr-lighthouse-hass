"""Identify button for SteamVR Lighthouse base stations."""

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import LighthouseConfigEntry
from .entity import LighthouseEntity

PARALLEL_UPDATES = 0

IDENTIFY = ButtonEntityDescription(
    key="identify",
    device_class=ButtonDeviceClass.IDENTIFY,
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LighthouseConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the identify button."""
    async_add_entities([LighthouseIdentifyButton(entry.runtime_data, IDENTIFY)])


class LighthouseIdentifyButton(LighthouseEntity, ButtonEntity):
    """Blinks the station's LED."""

    async def async_press(self) -> None:
        """Blink the LED."""
        await self.coordinator.async_run_command(self.coordinator.station.identify)
