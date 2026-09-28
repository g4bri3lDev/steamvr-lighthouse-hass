# SteamVR Lighthouse for Home Assistant

Control Valve Index (Lighthouse 2.0) base stations from Home Assistant over Bluetooth: switch
them on, to standby or to sleep, change their channel and see their state live.

Stations are found automatically. State comes straight from their Bluetooth advertisements, so
nothing is polled; a short connection is only opened when you send a command. Works with the
host's Bluetooth adapter and with ESPHome Bluetooth proxies.

HTC Vive (Lighthouse 1.0) base stations are not supported yet.

## Installation

1. In HACS, add `https://github.com/g4bri3lDev/steamvr-lighthouse-hass` as a custom repository
   (type: Integration) and install **SteamVR Lighthouse**.
2. Restart Home Assistant.
3. Stations in range appear under **Settings → Devices & services → Discovered**. Confirm each one.
   You can also add them via **Add integration → SteamVR Lighthouse**.

Each station's name (`LHB-…`) is printed on its back.

## Entities

| Entity | Description |
|---|---|
| Power (switch) | On wakes the station. Off puts it to sleep, or in standby if chosen in the options. |
| Power mode (select) | On, standby or sleep. |
| Power state (sensor) | On, booting, standby, sleep or unknown. Waking from sleep takes about 11 seconds and shows as booting. |
| Channel (select) | Tracking channel 1–16. |
| Identify (button) | Blinks the station's LED white for a few seconds. |
| Problem (binary sensor) | On when the station reports an error. |
| Signal strength (sensor) | Bluetooth RSSI; disabled by default. |

**Sleep** stops the rotors and saves the most power (LED pulses blue). **Standby** turns the
lasers off but keeps the rotors spinning, so the station is back within about a second.

## Options

**Turning the power switch off** — sleep (default) or standby. Stations whose firmware has no
standby always go to sleep.

## Troubleshooting

- **Station not discovered / unavailable:** a Bluetooth adapter or ESPHome proxy must be in range.
  Stations keep advertising while asleep, so they stay available.
- **Command failed ("could not reach"):** the station was out of range or all Bluetooth connection
  slots were busy; try again.
- Diagnostics (device page → Download diagnostics) include the raw advertisement bytes, with the
  address removed.

Built on the [`lighthouse-ble`](https://github.com/g4bri3lDev/lighthouse-ble) library.

## Trademarks

Steam, SteamVR, Valve and Valve Index are trademarks of Valve Corporation. The images in
`custom_components/steamvr_lighthouse/brand/` are Valve's brand assets; they are not covered by
this project's license. This is an unofficial integration, not affiliated with or endorsed by Valve.
