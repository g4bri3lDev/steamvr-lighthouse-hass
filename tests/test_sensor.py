"""Tests for the sensor platform."""

from unittest.mock import patch

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    snapshot_platform,
)
from syrupy.assertion import SnapshotAssertion

from . import ADDRESS, NAME, inject, payload, service_info, setup_integration

POWER_STATE = "sensor.lhb_747a9bc5_power_state"


@pytest.mark.usefixtures("entity_registry_enabled_by_default", "mock_station")
async def test_sensors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    with patch("custom_components.steamvr_lighthouse.PLATFORMS", [Platform.SENSOR]):
        await setup_integration(hass, config_entry)
    await snapshot_platform(hass, entity_registry, snapshot, config_entry.entry_id)


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        pytest.param(0x0B, "on", id="on"),
        pytest.param(0x02, "standby", id="standby"),
        pytest.param(0x00, "sleep", id="sleep"),
        pytest.param(0x08, "booting", id="waking_08"),
        pytest.param(0x01, "booting", id="waking_01"),
        pytest.param(0x09, "booting", id="waking_09"),
        pytest.param(0x77, "unknown", id="unknown_code"),
    ],
)
@pytest.mark.usefixtures("mock_station")
async def test_power_state_follows_advertisements(
    hass: HomeAssistant, config_entry: MockConfigEntry, code: int, expected: str
) -> None:
    await setup_integration(hass, config_entry)
    inject(hass, service_info(payload(power=code)))
    await hass.async_block_till_done()
    assert hass.states.get(POWER_STATE).state == expected


@pytest.mark.usefixtures("mock_station")
async def test_nameless_advertisement_updates_state(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    device_registry: dr.DeviceRegistry,
) -> None:
    await setup_integration(hass, config_entry)
    inject(hass, service_info(payload(power=0x00), name=ADDRESS))
    await hass.async_block_till_done()
    assert hass.states.get(POWER_STATE).state == "sleep"
    device = device_registry.async_get_device_by_connection(
        (dr.CONNECTION_BLUETOOTH, ADDRESS), config_entry.entry_id
    )
    assert device is not None
    assert device.name == NAME
