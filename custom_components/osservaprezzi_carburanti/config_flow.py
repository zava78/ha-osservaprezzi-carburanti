"""Config flow per osservaprezzi_carburanti.

Modulo minimo del Config Flow; fornito come scheletro estendibile.
"""
from __future__ import annotations

import logging
from typing import Any

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
import voluptuous as vol

from .const import DOMAIN, API_URL_TEMPLATE, REQUEST_TIMEOUT
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from .helpers import build_station_preview

_LOGGER = logging.getLogger(__name__)


def _parse_stations_field(value: str) -> list[dict]:
    """Parsa un campo multilinea/CSV contenente gli impianti in una lista di dict.

    Formati accettati per riga:
    - 48524
    - 48524,Distributore Ener Coop
    - 48524;Distributore Ener Coop
    La virgola o il punto e virgola separano l'id e il nome facoltativo. Le righe vuote vengono ignorate.
    """
    stations: list[dict] = []
    if not value:
        return stations
    for line in value.splitlines():
        raw = line.strip()
        if not raw:
            continue
        # prova prima la virgola poi il punto e virgola
        for sep in (",", ";"):
            if sep in raw:
                parts = [p.strip() for p in raw.split(sep, 1)]
                break
        else:
            parts = [raw]

        sid = parts[0]
        name = parts[1] if len(parts) > 1 else ""
        try:
            stations.append({"id": int(sid), "name": name})
        except Exception:
            # skip invalid ids
            _LOGGER.debug("Skipping invalid station id in config flow: %s", sid)
    return stations


class OsservaPrezziConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Osservaprezzi Carburanti."""

    VERSION = 2

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Passo iniziale: accetta più impianti come testo multilinea.

        Il campo `stations` accetta una riga per impianto nella forma `id[,name]`.
        """
        errors: dict[str, str] = {}
        if user_input is None:
            data_schema = vol.Schema(
                {
                    vol.Required("stations", default="48524"):
                    str,
                    vol.Optional("scan_interval", default=3600): int,
                    vol.Optional("title", default="Stazioni Osservaprezzi"): str,
                }
            )
            return self.async_show_form(step_id="user", data_schema=data_schema)

        stations_raw = user_input.get("stations", "")
        stations = _parse_stations_field(stations_raw)
        if not stations:
            errors["stations"] = "invalid_stations"

        # Validazione live: chiama l'API Osservaprezzi per ogni id impianto
        if not errors:
            session = async_get_clientsession(self.hass)
            invalid_ids: list[int] = []
            valid_stations: list[dict] = []
            preview_lines: list[str] = []

            for st in stations:
                sid = st.get("id")
                url = API_URL_TEMPLATE.format(id=sid)
                try:
                    async with session.get(url, timeout=REQUEST_TIMEOUT) as resp:
                        if resp.status != 200:
                            _LOGGER.debug("Validation: station %s returned status %s", sid, resp.status)
                            invalid_ids.append(sid)
                            continue
                        payload = await resp.json()
                        if not isinstance(payload, dict) or ("id" not in payload and "Id" not in payload):
                            _LOGGER.debug("Validazione: l'impianto %s ha restituito un payload inatteso", sid)
                            invalid_ids.append(sid)
                            continue

                        preview_line, station_entry = build_station_preview(payload, sid, st.get("name"))
                        preview_lines.append(preview_line)
                        valid_stations.append(station_entry)
                        # use provided name if present, otherwise API name
                        station_entry = {"id": int(sid), "name": st.get("name") or name}
                        valid_stations.append(station_entry)
                except Exception as exc:  # network/parse error -> mark invalid
                    _LOGGER.debug("Errore di validazione per l'impianto %s: %s", sid, exc)
                    invalid_ids.append(sid)

            if invalid_ids:
                # prepara la proposta per consentire all'utente di procedere solo con gli impianti validi
                invalid_list = ", ".join(str(i) for i in invalid_ids)
                _LOGGER.warning("Config flow: id impianto non validi: %s", invalid_list)
                # store validated subsets on the flow instance
                self._valid_stations = valid_stations
                self._invalid_ids = invalid_ids
                self._pending_scan_interval = int(user_input.get("scan_interval") or 3600)
                self._pending_title = user_input.get("title") or "Stazioni Osservaprezzi"
                self._preview_text = "\n".join(preview_lines)

                # ask user to confirm whether to proceed with valid stations only
                data_schema = vol.Schema({vol.Required("proceed", default=True): bool})
                return self.async_show_form(
                    step_id="confirm",
                    data_schema=data_schema,
                    description_placeholders={
                        "invalid_ids": invalid_list,
                        "valid_count": str(len(self._valid_stations)),
                        "preview": self._preview_text,
                    },
                )
        if errors:
            return self.async_show_form(step_id="user", data_schema=None, errors=errors)

        data = {
            "stations": stations,
            "scan_interval": int(user_input.get("scan_interval") or 3600),
            "title": user_input.get("title") or "Osservaprezzi stations",
        }

        title = data["title"]
        return self.async_create_entry(title=title, data=data)

    async def async_step_confirm(self, user_input: dict[str, Any] | None = None):
        """Confirmation step when some station IDs were invalid.

        If the user chooses to proceed, create the entry using only valid stations.
        """
        if user_input is None:
            data_schema = vol.Schema({vol.Required("proceed", default=True): bool})
            invalid_list = ", ".join(str(i) for i in getattr(self, "_invalid_ids", []))
            return self.async_show_form(
                step_id="confirm",
                data_schema=data_schema,
                description_placeholders={
                    "invalid_ids": invalid_list,
                    "valid_count": str(len(getattr(self, "_valid_stations", []))),
                },
            )

        proceed = bool(user_input.get("proceed"))
        if not proceed:
            return self.async_abort(reason="aborted_by_user")

        stations = getattr(self, "_valid_stations", [])
        if not stations:
            return self.async_abort(reason="aborted")

        data = {
            "stations": stations,
            "scan_interval": getattr(self, "_pending_scan_interval", 3600),
            "title": getattr(self, "_pending_title", "Osservaprezzi stations"),
        }
        title = data["title"]
        return self.async_create_entry(title=title, data=data)
