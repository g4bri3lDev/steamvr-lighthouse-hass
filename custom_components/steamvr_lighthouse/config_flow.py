"""Config flow for SteamVR Lighthouse."""

from typing import Any

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from lighthouse_ble import Version, parse_advertisement
import voluptuous as vol

from .const import CONF_OFF_ACTION, DEFAULT_OFF_ACTION, DOMAIN, OffAction


def _is_v2_station(info: BluetoothServiceInfoBleak) -> bool:
    advertisement = parse_advertisement(info.name, info.manufacturer_data)
    return advertisement is not None and advertisement.version is Version.V2


class SteamVRLighthouseConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SteamVR Lighthouse base stations."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._discovery: BluetoothServiceInfoBleak | None = None
        self._discovered: dict[str, str] = {}

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
        if user_input is not None:
            return self.async_create_entry(
                title=name, data={CONF_ADDRESS: self._discovery.address}
            )
        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm", description_placeholders={"name": name}
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Pick one of the stations currently in range."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self._discovered[address], data={CONF_ADDRESS: address}
            )

        configured = self._async_current_ids(include_ignore=False)
        for info in async_discovered_service_info(self.hass, connectable=True):
            if info.address not in configured and _is_v2_station(info):
                self._discovered[info.address] = info.name
        if not self._discovered:
            return self.async_abort(reason="no_devices_found")
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_ADDRESS): vol.In(self._discovered)}
            ),
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
