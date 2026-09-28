"""The SteamVR Lighthouse integration."""

from homeassistant.components.bluetooth import (
    async_ble_device_from_address,
    async_last_service_info,
)
from homeassistant.const import CONF_ADDRESS, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from lighthouse_ble import BaseStationState, BaseStationV2, parse_advertisement

from .const import DOMAIN
from .coordinator import LighthouseConfigEntry, LighthouseCoordinator

PLATFORMS: list[Platform] = [
    Platform.BUTTON,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: LighthouseConfigEntry) -> bool:
    """Set up a base station from a config entry."""
    address: str = entry.data[CONF_ADDRESS]
    ble_device = async_ble_device_from_address(hass, address, connectable=True)
    if ble_device is None:
        raise ConfigEntryNotReady(
            translation_domain=DOMAIN,
            translation_key="device_not_found",
            translation_placeholders={"name": entry.title},
        )
    info = async_last_service_info(hass, address, connectable=True)
    advertisement = (
        parse_advertisement(info.name, info.manufacturer_data) if info else None
    )
    station = BaseStationV2(ble_device, advertisement)
    coordinator = LighthouseCoordinator(hass, entry, station)
    entry.runtime_data = coordinator

    def _state_changed(_state: BaseStationState) -> None:
        coordinator.async_update_listeners()

    entry.async_on_unload(station.register_callback(_state_changed))
    entry.async_on_unload(coordinator.async_start())
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_create_background_task(
        hass, coordinator.async_update_device_info(), "steamvr_lighthouse_device_info"
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: LighthouseConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
