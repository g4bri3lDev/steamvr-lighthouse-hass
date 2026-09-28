"""Tests for the power mode and channel selects."""

from types import SimpleNamespace
from unittest.mock import PropertyMock, patch

from homeassistant.components.select import (
    ATTR_OPTION,
    ATTR_OPTIONS,
    DOMAIN as SELECT_DOMAIN,
    SERVICE_SELECT_OPTION,
)
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from lighthouse_ble import BaseStationV2, PowerState
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    snapshot_platform,
)
from syrupy.assertion import SnapshotAssertion

from . import inject, payload, service_info, setup_integration

POWER_MODE = "select.lhb_747a9bc5_power_mode"
CHANNEL = "select.lhb_747a9bc5_channel"


@pytest.mark.usefixtures("mock_station")
async def test_select_entities(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    with patch("custom_components.steamvr_lighthouse.PLATFORMS", [Platform.SELECT]):
        await setup_integration(hass, config_entry)
    await snapshot_platform(hass, entity_registry, snapshot, config_entry.entry_id)


@pytest.mark.parametrize(
    ("option", "expected"),
    [
        pytest.param("on", PowerState.ON, id="on"),
        pytest.param("standby", PowerState.STANDBY, id="standby"),
        pytest.param("sleep", PowerState.SLEEP, id="sleep"),
    ],
)
async def test_select_power_mode(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_station: SimpleNamespace,
    option: str,
    expected: PowerState,
) -> None:
    await setup_integration(hass, config_entry)
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: POWER_MODE, ATTR_OPTION: option},
        blocking=True,
    )
    mock_station.set_power.assert_awaited_once_with(expected)


@pytest.mark.parametrize(
    ("code", "expected"),
    [
        pytest.param(0x02, "standby", id="standby"),
        pytest.param(0x00, "sleep", id="sleep"),
        pytest.param(0x77, "unknown", id="unknown_code"),
    ],
)
@pytest.mark.usefixtures("mock_station")
async def test_power_mode_follows_advertisements(
    hass: HomeAssistant, config_entry: MockConfigEntry, code: int, expected: str
) -> None:
    await setup_integration(hass, config_entry)
    inject(hass, service_info(payload(power=code)))
    await hass.async_block_till_done()
    assert hass.states.get(POWER_MODE).state == expected


@pytest.mark.usefixtures("mock_station")
async def test_power_mode_hides_standby_on_legacy_firmware(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    await setup_integration(hass, config_entry)
    assert hass.states.get(POWER_MODE).attributes[ATTR_OPTIONS] == [
        "on",
        "standby",
        "sleep",
    ]
    with patch.object(
        BaseStationV2, "supports_standby", new_callable=PropertyMock, return_value=False
    ):
        inject(hass, service_info(payload(power=0x00)))
        await hass.async_block_till_done()
        assert hass.states.get(POWER_MODE).attributes[ATTR_OPTIONS] == ["on", "sleep"]


async def test_select_channel(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_station: SimpleNamespace
) -> None:
    await setup_integration(hass, config_entry)
    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: CHANNEL, ATTR_OPTION: "3"},
        blocking=True,
    )
    mock_station.set_channel.assert_awaited_once_with(3)


@pytest.mark.usefixtures("mock_station")
async def test_channel_follows_advertisement(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    await setup_integration(hass, config_entry)
    assert hass.states.get(CHANNEL).state == "1"
    inject(hass, service_info(payload(channel=2)))
    await hass.async_block_till_done()
    assert hass.states.get(CHANNEL).state == "2"
