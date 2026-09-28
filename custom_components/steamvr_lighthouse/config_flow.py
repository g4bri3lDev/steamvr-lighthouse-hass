"""Config flow for SteamVR Lighthouse."""

import asyncio
import logging
from typing import Any

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_ble_device_from_address,
    async_discovered_service_info,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from lighthouse_ble import BaseStationV2, LighthouseError, Version, parse_advertisement
import voluptuous as vol

from .const import CONF_OFF_ACTION, DEFAULT_OFF_ACTION, DOMAIN, OffAction

_LOGGER = logging.getLogger(__name__)

# A station that stops responding mid-check would otherwise hold the dialog and a
# connection slot indefinitely.
CONNECT_TIMEOUT = 45


def _is_v2_station(info: BluetoothServiceInfoBleak) -> bool:
    advertisement = parse_advertisement(info.name, info.manufacturer_data)
    return advertisement is not None and advertisement.version is Version.V2


async def _test_connection(hass: HomeAssistant, address: str) -> str | None:
    """Read the station's device information; return an error key on failure."""
    ble_device = async_ble_device_from_address(hass, address, connectable=True)
    if ble_device is None:
        return "cannot_connect"
    try:
        async with asyncio.timeout(CONNECT_TIMEOUT):
            await BaseStationV2(ble_device).read_device_info()
    except LighthouseError, TimeoutError:
        return "cannot_connect"
    except Exception:
        _LOGGER.exception("Unexpected error while connecting to %s", address)
        return "unknown"
    return None


class SteamVRLighthouseConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SteamVR Lighthouse base stations."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._discovery: BluetoothServiceInfoBleak | None = None
        self._discovered: dict[str, BluetoothServiceInfoBleak] = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow."""
        return SteamVRLighthouseOptionsFlow()

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a station found by the bluetooth integration."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        if not _is_v2_station(discovery_info):
            return self.async_abort(reason="not_supported")
        self._discovery = discovery_info
        self.context["title_placeholders"] = {"name": discovery_info.name}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm setting up a discovered station."""
        assert self._discovery is not None
        name = self._discovery.name
        errors: dict[str, str] = {}
        if user_input is not None:
            address = self._discovery.address
            if (error := await _test_connection(self.hass, address)) is None:
                return self.async_create_entry(title=name, data={CONF_ADDRESS: address})
            errors["base"] = error
        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"name": name},
            errors=errors,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick one of the stations currently in range."""
        errors: dict[str, str] = {}
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            if (error := await _test_connection(self.hass, address)) is None:
                return self.async_create_entry(
                    title=self._discovered[address].name, data={CONF_ADDRESS: address}
                )
            errors["base"] = error

        if not self._discovered:
            configured = self._async_current_ids(include_ignore=False)
            for info in async_discovered_service_info(self.hass, connectable=True):
                if info.address not in configured and _is_v2_station(info):
                    self._discovered[info.address] = info
        if not self._discovered:
            return self.async_abort(reason="no_devices_found")
        names = {
            address: f"{info.name} ({address})"
            for address, info in self._discovered.items()
        }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): vol.In(names)}),
            errors=errors,
        )


class SteamVRLighthouseOptionsFlow(OptionsFlow):
    """Options for a base station."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Choose what turning the power switch off does."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)
        current = self.config_entry.options.get(CONF_OFF_ACTION, DEFAULT_OFF_ACTION)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_OFF_ACTION, default=current): SelectSelector(
                        SelectSelectorConfig(
                            options=[action.value for action in OffAction],
                            translation_key=CONF_OFF_ACTION,
                            mode=SelectSelectorMode.LIST,
                        )
                    )
                }
            ),
        )
