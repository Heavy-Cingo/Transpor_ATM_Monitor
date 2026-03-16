import logging
import asyncio  # <-- ti serve per asyncio.TimeoutError
from datetime import timedelta

import aiohttp
from aiohttp import ClientError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
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

        # Mantengo il tuo entity_id personalizzato per compatibilità con automazioni esistenti
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
        return True  # ok: puoi forzare update_entity oltre al timer interno

    async def async_update(self, *_):
        """Fetch new state data for the sensor."""
        self._attr_extra_state_attributes = {
            "line": self._line,
            "busstopnumber": self._busstopnumber,
            "refreshsec": self._refreshsec,
        }
        new = await self.fetch_with_header()
        if new not in ("Error", None):
            self._state = new
            self._available = True
        else:
            # se l’API fallisce, segnalo non disponibile (evita confusione con il placeholder)
            self._available = False
        self.async_write_ha_state()

    async def fetch_with_header(self) -> str:
        """HTTP GET usando la sessione di Home Assistant (aiohttp), con header 'credibili'."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "it-IT,it;q=0.9",
            "Referer": "https://giromilano.atm.it/it",
            "Origin": "https://giromilano.atm.it",
        }

        url = (
            "https://giromilano.atm.it/proxy.tpportal/api/tpPortal/geodata/pois/stops/"
            + self._busstopnumber
        )

        session = async_get_clientsession(self.hass)
        timeout = aiohttp.ClientTimeout(total=10)

        try:
            async with session.get(url, headers=headers, timeout=timeout) as resp:
                if resp.status != 200:
                    _LOGGER.warning("ATM HTTP %s", resp.status)
                    return "Error"

                data = await resp.json(content_type=None)
                linee = data.get("Lines", [])

                for linea in linee:
                    # confronto come stringhe per evitare mismatch int/str
                    if str(linea["Line"]["LineId"]) == str(self._line):
                        return linea.get("WaitMessage", "No data")

                return "No data"

        except (ClientError, asyncio.TimeoutError) as e:
            _LOGGER.error("Errore di rete ATM: %s", e)
        except Exception as e:
            _LOGGER.error("Errore generico ATM: %s", e)

        return "Error"
