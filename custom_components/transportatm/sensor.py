import logging
from datetime import timedelta
import aiohttp

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

DOMAIN = "transportatm"
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    line = config_entry.data["Line"]
    busstopnumber = config_entry.data["Bus_Stop_Number"]
    refreshsec = config_entry.data["Refresh_Time_sec"]

    async_add_entities([TransportATMMonitor(line, busstopnumber, refreshsec)], True)


class TransportATMMonitor(SensorEntity):
    """Transport ATM sensor."""

    def __init__(self, line: str, busstopnumber: str, refreshsec: int):
        self._line = line
        self._busstopnumber = busstopnumber
        self._refreshsec = refreshsec
        self._state = None
        self._attr_extra_state_attributes = {}
        self._available = True

        self._attr_name = f"TransportATM {line} {busstopnumber}"
        self._unique_id = f"{DOMAIN}_{line}_{busstopnumber}"

    async def async_added_to_hass(self):
        """Schedule periodic update."""
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self.async_update, timedelta(seconds=self._refreshsec)
            )
        )

    @property
    def name(self):
        return self._attr_name

    @property
    def state(self):
        return self._state

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def available(self):
        return self._available

    async def async_update(self, *_):
        """Fetch data from ATM API."""
        url = f"https://giromilano.atm.it/proxy.tpportal/api/tpPortal/geodata/pois/stops/{self._busstopnumber}"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    if response.status != 200:
                        _LOGGER.warning("HTTP error %s", response.status)
                        self._state = "Error"
                        return
                    data = await response.json()
                    lines = data.get("Lines", [])
                    value = next(
                        (line_item["WaitMessage"] for line_item in lines if line_item["Line"]["LineId"] == self._line),
                        None
                    )
                    self._state = value if value else "No data"
        except Exception as e:
            _LOGGER.error("Error fetching ATM data: %s", e)
            self._state = "Error"
        finally:
            self.async_write_ha_state()
