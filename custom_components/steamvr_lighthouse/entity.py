"""Base entity for SteamVR Lighthouse."""

from homeassistant.components.bluetooth.passive_update_coordinator import (
    PassiveBluetoothCoordinatorEntity,
)
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity import EntityDescription
from lighthouse_ble import BaseStationState

from .coordinator import LighthouseCoordinator


class LighthouseEntity(PassiveBluetoothCoordinatorEntity[LighthouseCoordinator]):
    """An entity belonging to one base station."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: LighthouseCoordinator, description: EntityDescription
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.address}_{description.key}"
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, coordinator.address)},
            name=coordinator.entry.title,
            manufacturer="Valve",
        )

    @property
    def station_state(self) -> BaseStationState:
        """Return the station's last known state."""
        return self.coordinator.station.state
