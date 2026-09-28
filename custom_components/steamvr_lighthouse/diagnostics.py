"""Diagnostics for SteamVR Lighthouse."""

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant

from .coordinator import LighthouseConfigEntry

TO_REDACT = {CONF_ADDRESS, "unique_id", "discovery_keys"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: LighthouseConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    advertisement = coordinator.last_advertisement
    raw = advertisement.raw if advertisement is not None else None
    return {
        "entry": async_redact_data(entry.as_dict(), TO_REDACT),
        "state": asdict(coordinator.station.state),
        "supports_standby": coordinator.station.supports_standby,
        "last_advertisement_raw": raw.hex() if raw is not None else None,
        "rssi": coordinator.rssi,
        "available": coordinator.available,
    }
