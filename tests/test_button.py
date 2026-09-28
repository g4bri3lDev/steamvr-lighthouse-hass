"""Tests for the identify button."""

from types import SimpleNamespace
from unittest.mock import patch

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.const import ATTR_ENTITY_ID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    snapshot_platform,
)
from syrupy.assertion import SnapshotAssertion

from . import setup_integration

IDENTIFY = "button.lhb_747a9bc5_identify"


@pytest.mark.usefixtures("mock_station")
async def test_button_entities(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    with patch("custom_components.steamvr_lighthouse.PLATFORMS", [Platform.BUTTON]):
        await setup_integration(hass, config_entry)
    await snapshot_platform(hass, entity_registry, snapshot, config_entry.entry_id)


async def test_identify(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_station: SimpleNamespace
) -> None:
    await setup_integration(hass, config_entry)
    await hass.services.async_call(
        BUTTON_DOMAIN, SERVICE_PRESS, {ATTR_ENTITY_ID: IDENTIFY}, blocking=True
    )
    mock_station.identify.assert_awaited_once_with()
