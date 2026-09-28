"""Tests for the SteamVR Lighthouse integration."""

import time

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_get_advertisement_callback,
)
from homeassistant.core import HomeAssistant

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
