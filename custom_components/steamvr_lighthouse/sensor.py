"""Sensors for SteamVR Lighthouse base stations."""

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import SIGNAL_STRENGTH_DECIBELS_MILLIWATT, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType
from lighthouse_ble import PowerState

from .coordinator import LighthouseConfigEntry, LighthouseCoordinator
from .entity import LighthouseEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class LighthouseSensorDescription(SensorEntityDescription):
    """Describes a base station sensor."""

    value_fn: Callable[[LighthouseCoordinator], StateType]


def _power_state(coordinator: LighthouseCoordinator) -> str | None:
    power = coordinator.station.state.power
    return power.value if power is not None else None


SENSORS: tuple[LighthouseSensorDescription, ...] = (
    LighthouseSensorDescription(
        key="power_state",
        translation_key="power_state",
        device_class=SensorDeviceClass.ENUM,
        options=[state.value for state in PowerState],
        value_fn=_power_state,
    ),
    LighthouseSensorDescription(
        key="rssi",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda coordinator: coordinator.rssi,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: LighthouseConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensors."""
    coordinator = entry.runtime_data
    async_add_entities(
        LighthouseSensor(coordinator, description) for description in SENSORS
    )


class LighthouseSensor(LighthouseEntity, SensorEntity):
    """A base station sensor."""

    entity_description: LighthouseSensorDescription

    @property
    def native_value(self) -> StateType:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.coordinator)
