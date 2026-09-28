"""Constants for the SteamVR Lighthouse integration."""

from enum import StrEnum
from typing import Final

DOMAIN: Final = "steamvr_lighthouse"

CONF_OFF_ACTION: Final = "off_action"


class OffAction(StrEnum):
    """What turning the power switch off sends."""

    SLEEP = "sleep"
    STANDBY = "standby"


DEFAULT_OFF_ACTION: Final = OffAction.SLEEP
