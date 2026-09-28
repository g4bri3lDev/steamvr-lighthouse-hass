"""Tests for the SteamVR Lighthouse integration."""

from collections.abc import Iterator
from contextlib import contextmanager
import time
from unittest.mock import patch

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_get_advertisement_callback,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

ADDRESS = "AA:BB:CC:DD:EE:01"
NAME = "LHB-747A9BC5"
VALVE = 1373


def payload(power: int = 0x0B, channel: int = 1, fault: int = 0) -> bytes:
    """Build a V2 advertisement payload in the layout real stations send."""
    return bytes([0x00, 0x02, channel, 0x01, power, 0x06, fault])


ON_CH1 = payload()


def service_info(
    data: bytes | None = ON_CH1,
    *,
    name: str = NAME,
    address: str = ADDRESS,
    rssi: int = -60,
) -> BluetoothServiceInfoBleak:
    """Build a service info as HA's bluetooth integration would deliver it."""
    manufacturer_data = {} if data is None else {VALVE: data}
    advertisement = AdvertisementData(
        local_name=name,
        manufacturer_data=manufacturer_data,
        service_data={},
        service_uuids=[],
        tx_power=-127,
        rssi=rssi,
        platform_data=(),
    )
    return BluetoothServiceInfoBleak(
        name=name,
        address=address,
        rssi=rssi,
        manufacturer_data=manufacturer_data,
        service_data={},
        service_uuids=[],
        source="local",
        device=BLEDevice(address, name, {}),
        advertisement=advertisement,
        connectable=True,
        time=time.monotonic(),
        tx_power=-127,
    )


def inject(hass: HomeAssistant, info: BluetoothServiceInfoBleak) -> None:
    """Feed an advertisement into HA's bluetooth manager."""
    async_get_advertisement_callback(hass)(info)


async def setup_integration(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Make the station visible to HA, then set up the entry."""
    await async_setup_component(hass, "bluetooth", {})
    inject(hass, service_info())
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)


@contextmanager
def patch_bluetooth_time(mock_time: float) -> Iterator[None]:
    """Pretend the bluetooth stack's clock is at mock_time."""
    with (
        patch(
            "homeassistant.components.bluetooth.MONOTONIC_TIME", return_value=mock_time
        ),
        patch("habluetooth.base_scanner.monotonic_time_coarse", return_value=mock_time),
        patch("habluetooth.manager.monotonic_time_coarse", return_value=mock_time),
        patch("habluetooth.scanner.monotonic_time_coarse", return_value=mock_time),
    ):
        yield
