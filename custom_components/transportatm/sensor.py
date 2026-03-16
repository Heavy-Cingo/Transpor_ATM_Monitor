import logging
import asyncio  # <-- ti serve per asyncio.TimeoutError
import random
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
        """HTTP GET usando la sessione HA con priming cookie, header completi e backoff anti-403."""

        session = async_get_clientsession(self.hass)
        timeout = aiohttp.ClientTimeout(total=12)

        # URL principali
        home_url = "https://giromilano.atm.it/it"  # priming cookie
        api_url = (
            "https://giromilano.atm.it/proxy.tpportal/api/tpPortal/geodata/pois/stops/"
            + self._busstopnumber
        )

        # Header “credibili”
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/121.0.0.0 Safari/537.36"
            ),
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "Referer": "https://giromilano.atm.it/it",
            "Origin": "https://giromilano.atm.it",
            # Alcuni endpoint accettano meglio richieste XHR:
            "X-Requested-With": "XMLHttpRequest",
        }

        # 1) Priming cookie (non fallire se dà errore; serve solo a popolare i cookie della sessione)
        try:
            async with session.get(
                home_url,
                headers={
                    **headers,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                timeout=timeout,
            ) as resp:
                _ = await resp.text()
        except Exception as exc:
            _LOGGER.debug("Priming cookie fallito (ignoro): %s", exc)

        # 2) Tentativi con backoff + jitter
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                # jitter per evitare colpi sincronizzati se hai più entità
                await asyncio.sleep(random.uniform(0.1, 0.4))

                async with session.get(api_url, headers=headers, timeout=timeout) as resp:
                    if resp.status in (403, 429):
                        if attempt < max_attempts:
                            _LOGGER.warning("ATM HTTP %s (tentativo %s)", resp.status, attempt)
                            # prima dell’ultimo tentativo, ripeti il priming
                            if attempt == max_attempts - 1:
                                try:
                                    async with session.get(home_url, headers=headers, timeout=timeout) as r2:
                                        _ = await r2.text()
                                except Exception as exc2:
                                    _LOGGER.debug("Priming extra fallito (ignoro): %s", exc2)
                            await asyncio.sleep(0.6 * attempt)  # 0.6s, 1.2s
                            continue
                        # ultimo tentativo fallito: logga un estratto del body e termina
                        text = await resp.text()
                        _LOGGER.error("ATM %s risposta: %s", resp.status, text[:250])
                        return "Error"

                    resp.raise_for_status()
                    data = await resp.json(content_type=None)

                    # Estrai il WaitMessage per la linea richiesta
                    for linea in data.get("Lines", []):
                        li = linea.get("Line") or {}
                        if str(li.get("LineId")) == str(self._line):
                            return linea.get("WaitMessage", "No data")

                    return "No data"

            except (ClientError, asyncio.TimeoutError) as e:
                if attempt < max_attempts:
                    _LOGGER.debug("Errore di rete (tentativo %s): %s", attempt, e)
                    await asyncio.sleep(0.6 * attempt)
                    continue
                _LOGGER.error("Errore di rete definitivo: %s", e)
                return "Error"
            except Exception as e:
                if attempt < max_attempts:
                    _LOGGER.debug("Eccezione inattesa (tentativo %s): %s", attempt, e)
                    await asyncio.sleep(0.6 * attempt)
                    continue
                _LOGGER.error("Eccezione inattesa definitiva: %s", e)
                return "Error"

        return "Error"
