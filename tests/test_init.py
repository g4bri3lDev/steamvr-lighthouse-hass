"""Tests for setting up and unloading a base station."""

from datetime import timedelta
import time
from types import SimpleNamespace

from homeassistant.components.bluetooth import (
    FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from lighthouse_ble import LighthouseConnectionError
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from . import (
    ADDRESS,
    NAME,
    inject,
    patch_bluetooth_time,
    service_info,
    setup_integration,
)
from .conftest import DEVICE_INFO

POWER_STATE = "sensor.lhb_747a9bc5_power_state"


@pytest.mark.usefixtures("mock_station")
async def test_setup_and_unload(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    await setup_integration(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.NOT_LOADED


@pytest.mark.usefixtures("mock_station")
async def test_setup_retries_without_device(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    await async_setup_component(hass, "bluetooth", {})
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


@pytest.mark.usefixtures("mock_station")
async def test_device_info_updated(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    await setup_integration(hass, config_entry)
    device = device_registry.async_get_device_by_connection(
        (dr.CONNECTION_BLUETOOTH, ADDRESS), config_entry.entry_id
    )
    assert device is not None
    assert device.name == NAME
    assert device.manufacturer == "Valve"
    assert device.model == "Base Station 2.0"
    assert device.model_id == DEVICE_INFO.model
    assert device.sw_version == DEVICE_INFO.firmware
    assert device.hw_version == DEVICE_INFO.hardware
    assert device.serial_number == DEVICE_INFO.serial


async def test_device_info_failure_is_ignored(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
    mock_station: SimpleNamespace,
) -> None:
    mock_station.read_device_info.side_effect = LighthouseConnectionError(
        "out of range"
    )
    await setup_integration(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED
    device = device_registry.async_get_device_by_connection(
        (dr.CONNECTION_BLUETOOTH, ADDRESS), config_entry.entry_id
    )
    assert device is not None
    assert device.model == "Base Station 2.0"
    assert device.model_id is None
    assert device.sw_version is None


@pytest.mark.usefixtures("mock_station")
async def test_unavailable_and_recovery(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    start = time.monotonic()
    await setup_integration(hass, config_entry)
    assert hass.states.get(POWER_STATE).state == "on"

    stale = FALLBACK_MAXIMUM_STALE_ADVERTISEMENT_SECONDS + 1
    with patch_bluetooth_time(start + stale):
        async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=stale))
        await hass.async_block_till_done()
    assert hass.states.get(POWER_STATE).state == STATE_UNAVAILABLE

    inject(hass, service_info())
    await hass.async_block_till_done()
    assert hass.states.get(POWER_STATE).state == "on"
