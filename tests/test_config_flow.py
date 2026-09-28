"""Tests for the config and options flow."""

from types import SimpleNamespace
from unittest.mock import patch

from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from lighthouse_ble import LighthouseConnectionError
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.steamvr_lighthouse.const import DOMAIN

from . import ADDRESS, NAME, service_info

DISCOVERED = (
    "custom_components.steamvr_lighthouse.config_flow.async_discovered_service_info"
)
OTHER_ADDRESS = "AA:BB:CC:DD:EE:07"


async def test_bluetooth_discovery(
    hass: HomeAssistant, mock_station: SimpleNamespace
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info()
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"
    assert result["description_placeholders"] == {"name": NAME}

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == NAME
    assert result["data"] == {CONF_ADDRESS: ADDRESS}
    assert result["result"].unique_id == ADDRESS
    mock_station.read_device_info.assert_awaited_once()


async def test_bluetooth_confirm_cannot_connect(
    hass: HomeAssistant, mock_station: SimpleNamespace
) -> None:
    mock_station.read_device_info.side_effect = LighthouseConnectionError("no slot")
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info()
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"
    assert result["errors"] == {"base": "cannot_connect"}

    mock_station.read_device_info.side_effect = None
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_bluetooth_discovery_without_payload(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info(None)
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"


async def test_bluetooth_discovery_already_configured(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info()
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize(
    "name",
    [
        pytest.param("Steam Controller", id="other_valve_device"),
        pytest.param("LHB-00000000", id="boot_placeholder"),
    ],
)
async def test_bluetooth_discovery_not_lighthouse(
    hass: HomeAssistant, name: str
) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_BLUETOOTH}, data=service_info(name=name)
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "not_supported"


@pytest.mark.usefixtures("mock_station")
async def test_user_step_lists_discovered(hass: HomeAssistant) -> None:
    discovered = [
        service_info(),
        service_info(None, name="Pixel 9", address=OTHER_ADDRESS),
    ]
    with patch(DISCOVERED, return_value=discovered):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    address_field = result["data_schema"].schema[CONF_ADDRESS]
    assert address_field.container == {ADDRESS: NAME}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == NAME
    assert result["data"] == {CONF_ADDRESS: ADDRESS}


async def test_user_step_cannot_connect(
    hass: HomeAssistant, mock_station: SimpleNamespace
) -> None:
    mock_station.read_device_info.side_effect = LighthouseConnectionError("no slot")
    with patch(DISCOVERED, return_value=[service_info()]):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}

    mock_station.read_device_info.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_ADDRESS: ADDRESS}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == NAME


@pytest.mark.parametrize(
    "configured",
    [
        pytest.param(False, id="nothing_discovered"),
        pytest.param(True, id="already_set_up"),
    ],
)
async def test_user_step_no_devices(
    hass: HomeAssistant, config_entry: MockConfigEntry, configured: bool
) -> None:
    config_entry.add_to_hass(hass)
    discovered = [service_info()] if configured else []
    with patch(DISCOVERED, return_value=discovered):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_options_flow(hass: HomeAssistant, config_entry: MockConfigEntry) -> None:
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"off_action": "standby"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {"off_action": "standby"}
