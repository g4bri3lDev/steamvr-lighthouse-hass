"""Tests for the power switch and command error handling."""

from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import PropertyMock, patch

from homeassistant.components.button import DOMAIN as BUTTON_DOMAIN, SERVICE_PRESS
from homeassistant.components.select import (
    ATTR_OPTION,
    DOMAIN as SELECT_DOMAIN,
    SERVICE_SELECT_OPTION,
)
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from lighthouse_ble import (
    BaseStationV2,
    LighthouseConnectionError,
    LighthouseError,
    PowerState,
    UnsupportedError,
)
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    snapshot_platform,
)
from syrupy.assertion import SnapshotAssertion

from . import inject, make_entry, payload, service_info, setup_integration

SWITCH = "switch.lhb_747a9bc5_power"
POWER_MODE = "select.lhb_747a9bc5_power_mode"
CHANNEL = "select.lhb_747a9bc5_channel"
IDENTIFY = "button.lhb_747a9bc5_identify"


@pytest.mark.usefixtures("mock_station")
async def test_switch_entities(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    snapshot: SnapshotAssertion,
) -> None:
    with patch("custom_components.steamvr_lighthouse.PLATFORMS", [Platform.SWITCH]):
        await setup_integration(hass, config_entry)
    await snapshot_platform(hass, entity_registry, snapshot, config_entry.entry_id)


async def test_turn_on(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_station: SimpleNamespace
) -> None:
    await setup_integration(hass, config_entry)
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: SWITCH}, blocking=True
    )
    mock_station.set_power.assert_awaited_once_with(PowerState.ON)


@pytest.mark.parametrize(
    ("options", "expected"),
    [
        pytest.param(None, PowerState.SLEEP, id="default"),
        pytest.param({"off_action": "sleep"}, PowerState.SLEEP, id="sleep"),
        pytest.param({"off_action": "standby"}, PowerState.STANDBY, id="standby"),
    ],
)
async def test_turn_off(
    hass: HomeAssistant,
    mock_station: SimpleNamespace,
    options: dict[str, str] | None,
    expected: PowerState,
) -> None:
    await setup_integration(hass, make_entry(options))
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: SWITCH}, blocking=True
    )
    mock_station.set_power.assert_awaited_once_with(expected)


async def test_turn_off_standby_unsupported(
    hass: HomeAssistant, mock_station: SimpleNamespace
) -> None:
    with patch.object(
        BaseStationV2, "supports_standby", new_callable=PropertyMock, return_value=False
    ):
        await setup_integration(hass, make_entry({"off_action": "standby"}))
        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: SWITCH}, blocking=True
        )
    mock_station.set_power.assert_awaited_once_with(PowerState.SLEEP)


async def test_switch_off_follows_option_change(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_station: SimpleNamespace
) -> None:
    await setup_integration(hass, config_entry)
    hass.config_entries.async_update_entry(
        config_entry, options={"off_action": "standby"}
    )
    await hass.async_block_till_done()
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: SWITCH}, blocking=True
    )
    mock_station.set_power.assert_awaited_once_with(PowerState.STANDBY)


@pytest.mark.usefixtures("mock_station")
async def test_booting_counts_as_on(
    hass: HomeAssistant, config_entry: MockConfigEntry
) -> None:
    await setup_integration(hass, config_entry)
    inject(hass, service_info(payload(power=0x08)))
    await hass.async_block_till_done()
    assert hass.states.get(SWITCH).state == STATE_ON
    assert hass.states.get(POWER_MODE).state == "on"


@pytest.mark.parametrize(
    ("domain", "service", "data", "method", "error", "key"),
    [
        pytest.param(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: SWITCH},
            "set_power",
            LighthouseConnectionError("gone"),
            "cannot_connect",
            id="switch",
        ),
        pytest.param(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: POWER_MODE, ATTR_OPTION: "sleep"},
            "set_power",
            LighthouseConnectionError("gone"),
            "cannot_connect",
            id="power_mode",
        ),
        pytest.param(
            SELECT_DOMAIN,
            SERVICE_SELECT_OPTION,
            {ATTR_ENTITY_ID: CHANNEL, ATTR_OPTION: "3"},
            "set_channel",
            LighthouseConnectionError("gone"),
            "cannot_connect",
            id="channel",
        ),
        pytest.param(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: IDENTIFY},
            "identify",
            LighthouseConnectionError("gone"),
            "cannot_connect",
            id="identify",
        ),
        pytest.param(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: SWITCH},
            "set_power",
            UnsupportedError("old firmware"),
            "not_supported",
            id="unsupported",
        ),
    ],
)
async def test_command_errors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_station: SimpleNamespace,
    domain: str,
    service: str,
    data: dict[str, str],
    method: str,
    error: LighthouseError,
    key: str,
) -> None:
    await setup_integration(hass, config_entry)
    getattr(mock_station, method).side_effect = error
    with pytest.raises(HomeAssistantError) as raised:
        await hass.services.async_call(domain, service, data, blocking=True)
    assert raised.value.translation_key == key
    assert hass.states.get(SWITCH).state == STATE_ON


async def test_turn_off_falls_back_to_sleep_when_standby_unsupported(
    hass: HomeAssistant, mock_station: SimpleNamespace
) -> None:
    # Firmware generation is only known after the first command connects.
    mock_station.set_power.side_effect = [UnsupportedError("no standby"), None]
    await setup_integration(hass, make_entry({"off_action": "standby"}))
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: SWITCH}, blocking=True
    )
    assert [call.args for call in mock_station.set_power.await_args_list] == [
        (PowerState.STANDBY,),
        (PowerState.SLEEP,),
    ]


async def test_switch_state_follows_commands(
    hass: HomeAssistant, config_entry: MockConfigEntry, mock_station: SimpleNamespace
) -> None:
    await setup_integration(hass, config_entry)
    station = config_entry.runtime_data.station

    async def apply(target: PowerState) -> None:
        station._set_state(replace(station.state, power=target, assumed=True))

    mock_station.set_power.side_effect = apply
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: SWITCH}, blocking=True
    )
    assert hass.states.get(SWITCH).state == STATE_OFF

    mock_station.set_power.side_effect = LighthouseConnectionError("gone")
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: SWITCH}, blocking=True
        )
    assert hass.states.get(SWITCH).state == STATE_OFF
