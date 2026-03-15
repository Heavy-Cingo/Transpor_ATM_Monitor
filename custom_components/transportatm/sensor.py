import logging
import httpx
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval

DOMAIN = "transport_atm_monitor"
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
    """Representation of the ATM transport sensor."""

    def __init__(self, line: str, busstopnumber: str, refreshsec: int):
        """Initialize the sensor."""
        self._available = True
        self._line = line
        self._busstopnumber = busstopnumber
        self._refreshsec = refreshsec

        self.entity_id = f"sensor.transportatm{line}{busstopnumber}"
        self._attr_name = f"TransportATM {line} {busstopnumber}"
        self._unique_id = f"{DOMAIN}_{self.entity_id}"

        self._state = "Wait in calculation"
        self._attr_extra_state_attributes = {
            "line": self._line,
            "busstopnumber": self._busstopnumber,
            "refreshsec": self._refreshsec,
        }

    async def async_added_to_hass(self):
        """Register periodic update callback."""
        self.async_on_remove(
            async_track_time_interval(
                self.hass, self.async_update, timedelta(seconds=self._refreshsec)
            )
        )

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._attr_name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return None

    @property
    def unique_id(self):
        return self._unique_id

    @property
    def available(self):
        """Return True if entity is available."""
        return self._available

    @property
    def should_poll(self) -> bool:
        """Enable manual update via homeassistant.update_entity."""
        return True

    async def async_update(self, *_):
        """Fetch new state data for the sensor."""
        self._attr_extra_state_attributes = {
            "line": self._line,
            "busstopnumber": self._busstopnumber,
            "refreshsec": self._refreshsec,
        }
        self._state = await self.fetch_with_header()
        self.async_write_ha_state()

    async def fetch_with_header(self) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
        }
        url = (
            "https://giromilano.atm.it/proxy.tpportal/api/tpPortal/geodata/pois/stops/"
            + self._busstopnumber
        )
        async with httpx.AsyncClient() as session:
            try:
                response = await session.get(url, headers=headers)
                if response.status_code != 200:
                    return "Error"
                data = response.json()
                linee = data["Lines"]
                kk = None
                for linea in linee:
                    if linea["Line"]["LineId"] == self._line:
                        kk = linea["WaitMessage"]
                        break
                return kk if kk is not None else "No data"
            except httpx.HTTPStatusError as e:
                _LOGGER.error(
                    f"Errore HTTP: {e.response.status_code} - {e.response.text}"
                )
            except httpx.RequestError as e:
                _LOGGER.error(f"Errore di connessione: {e}")
            except Exception as e:
                _LOGGER.error(f"Errore generico: {e}")
        return "Error"
