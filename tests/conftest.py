"""Fixtures for SteamVR Lighthouse tests."""

from collections.abc import Generator
from types import SimpleNamespace
from unittest.mock import AsyncMock, PropertyMock, patch

from lighthouse_ble import BaseStationV2, DeviceInfo
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.syrupy import HomeAssistantSnapshotExtension
from syrupy.assertion import SnapshotAssertion

from . import make_entry

DEVICE_INFO = DeviceInfo(
    model="1004",
    serial="FB92001DB6 V001017-20.A",
    firmware="R: 2.9.2004771 M: 1.8.2004742 B: 3.4.3782793",
    hardware="0.0",
    manufacturer="Valve Corp.",
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading the custom integration."""


@pytest.fixture(autouse=True)
def auto_mock_bluetooth(mock_bluetooth: None) -> None:
    """Keep the bluetooth stack from touching real adapters."""


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """Serialize Home Assistant objects deterministically in snapshots."""
    return snapshot.use_extension(HomeAssistantSnapshotExtension)


@pytest.fixture
def entity_registry_enabled_by_default() -> Generator[None]:
    """Enable entities that are disabled by default."""
    with patch(
        "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
        new_callable=PropertyMock,
        return_value=True,
    ):
        yield


@pytest.fixture
def mock_station() -> Generator[SimpleNamespace]:
    """Replace the station's Bluetooth I/O; state updates stay real."""
    mocks = SimpleNamespace(
        set_power=AsyncMock(),
        set_channel=AsyncMock(),
        identify=AsyncMock(),
        read_device_info=AsyncMock(return_value=DEVICE_INFO),
    )
    with (
        patch.object(BaseStationV2, "set_power", mocks.set_power),
        patch.object(BaseStationV2, "set_channel", mocks.set_channel),
        patch.object(BaseStationV2, "identify", mocks.identify),
        patch.object(BaseStationV2, "read_device_info", mocks.read_device_info),
    ):
        yield mocks


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """Return a config entry for the test station."""
    return make_entry()
