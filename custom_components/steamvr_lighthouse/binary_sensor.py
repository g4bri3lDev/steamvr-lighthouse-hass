"""Fault sensor for SteamVR Lighthouse base stations."""

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import LighthouseConfigEntry
from .entity import LighthouseEntity

PARALLEL_UPDATES = 0

FAULT = BinarySensorEntityDescription(
    key="fault",
    device_class=BinarySensorDeviceClass.PROBLEM,
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LighthouseConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the fault sensor."""
    async_add_entities([LighthouseFaultSensor(entry.runtime_data, FAULT)])


class LighthouseFaultSensor(LighthouseEntity, BinarySensorEntity):
    """On when the station reports an error (red LED)."""

    @property
    def is_on(self) -> bool | None:
        """Return True if the station reports a fault."""
        return self.station_state.faulty
