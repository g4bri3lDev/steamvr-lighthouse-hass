"""Tests for the notice pointing to the built-in integration."""

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.steamvr_lighthouse.const import DOMAIN

from . import setup_integration


@pytest.mark.usefixtures("mock_station")
async def test_deprecation_issue(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    issue_registry: ir.IssueRegistry,
) -> None:
    await setup_integration(hass, config_entry)
    assert issue_registry.async_get_issue(DOMAIN, "deprecated")

    assert await hass.config_entries.async_remove(config_entry.entry_id)
    assert issue_registry.async_get_issue(DOMAIN, "deprecated") is None


@pytest.mark.usefixtures("mock_station")
async def test_deprecation_issue_kept_for_remaining_stations(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    issue_registry: ir.IssueRegistry,
) -> None:
    other = MockConfigEntry(
        domain=DOMAIN, unique_id="AA:BB:CC:DD:EE:02", data=config_entry.data
    )
    other.add_to_hass(hass)
    await setup_integration(hass, config_entry)

    assert await hass.config_entries.async_remove(config_entry.entry_id)
    assert issue_registry.async_get_issue(DOMAIN, "deprecated")
