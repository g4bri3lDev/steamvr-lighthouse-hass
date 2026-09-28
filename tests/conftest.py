"""Fixtures for SteamVR Lighthouse tests."""

from homeassistant.const import CONF_ADDRESS
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.steamvr_lighthouse.const import DOMAIN

from . import ADDRESS, NAME


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading the custom integration."""


@pytest.fixture(autouse=True)
def auto_mock_bluetooth(mock_bluetooth: None) -> None:
    """Keep the bluetooth stack from touching real adapters."""


@pytest.fixture
def config_entry() -> MockConfigEntry:
    """Return a config entry for the test station."""
    return MockConfigEntry(
        domain=DOMAIN, unique_id=ADDRESS, data={CONF_ADDRESS: ADDRESS}, title=NAME
    )
