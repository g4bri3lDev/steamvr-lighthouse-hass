"""Coordinator for a SteamVR Lighthouse base station."""

from collections.abc import Awaitable, Callable
import logging
from typing import override

from homeassistant.components.bluetooth import (
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
)
from homeassistant.components.bluetooth.passive_update_coordinator import (
    PassiveBluetoothDataUpdateCoordinator,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from lighthouse_ble import (
    BaseStationV2,
    LighthouseAdvertisement,
    LighthouseConnectionError,
    LighthouseError,
    UnsupportedError,
    parse_advertisement,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

type LighthouseConfigEntry = ConfigEntry[LighthouseCoordinator]


class LighthouseCoordinator(PassiveBluetoothDataUpdateCoordinator):
    """Feeds advertisements to one base station and runs its commands."""

    def __init__(
        self, hass: HomeAssistant, entry: LighthouseConfigEntry, station: BaseStationV2
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            entry.data[CONF_ADDRESS],
            BluetoothScanningMode.PASSIVE,
            connectable=True,
        )
        self.entry = entry
        self.station = station
        self.rssi: int | None = None
        self.last_advertisement: LighthouseAdvertisement | None = None

    @callback
    @override
    def _async_handle_bluetooth_event(
        self, service_info: BluetoothServiceInfoBleak, change: BluetoothChange
    ) -> None:
        """Update the station from an advertisement."""
        self.station.set_ble_device(service_info.device)
        self.rssi = service_info.rssi
        advertisement = parse_advertisement(
            service_info.name, service_info.manufacturer_data
        )
        if advertisement is not None:
            self.last_advertisement = advertisement
            self.station.update_from_advertisement(advertisement)
        super()._async_handle_bluetooth_event(service_info, change)

    async def async_run_command(self, command: Callable[[], Awaitable[None]]) -> None:
        """Run a station command, translating library errors for the UI."""
        placeholders = {"name": self.entry.title}
        try:
            await command()
        except LighthouseConnectionError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="cannot_connect",
                translation_placeholders=placeholders,
            ) from err
        except UnsupportedError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="not_supported",
                translation_placeholders=placeholders,
            ) from err

    async def async_update_device_info(self) -> None:
        """Read model, firmware and serial once and store them on the device."""
        try:
            info = await self.station.read_device_info()
        except LighthouseError as err:
            _LOGGER.debug(
                "Could not read device information from %s: %s", self.entry.title, err
            )
            return
        registry = dr.async_get(self.hass)
        device = registry.async_get_device_by_connection(
            (dr.CONNECTION_BLUETOOTH, self.address), self.entry.entry_id
        )
        if device is None:
            return
        registry.async_update_device(
            device.id,
            model=info.model,
            sw_version=info.firmware,
            hw_version=info.hardware,
            serial_number=info.serial,
        )
