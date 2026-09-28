"""Tests for the fault binary sensor."""

from unittest.mock import patch

from homeassistant.const import STATE_OFF, STATE_ON, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    snapshot_platform,
)
from syrupy.assertion import SnapshotAssertion

from . import inject, payload, service_info, setup_integration

FAULT = "binary_sensor.lhb_747a9bc5_problem"


@pytest.mark.usefixtures("mock_station")
async def test_binary_sensor_entities(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    with patch(
        "custom_components.steamvr_lighthouse.PLATFORMS", [Platform.BINARY_SENSOR]
    ):
        await setup_integration(hass, config_entry)
    await snapshot_platform(hass, entity_registry, snapshot, config_entry.entry_id)


@pytest.mark.parametrize(
    ("fault", "expected"),
    [pytest.param(0, STATE_OFF, id="ok"), pytest.param(1, STATE_ON, id="fault")],
)
@pytest.mark.usefixtures("mock_station")
async def test_fault(
    hass: HomeAssistant, config_entry: MockConfigEntry, fault: int, expected: str
) -> None:
    await setup_integration(hass, config_entry)
    inject(hass, service_info(payload(fault=fault)))
    await hass.async_block_till_done()
    assert hass.states.get(FAULT).state == expected
