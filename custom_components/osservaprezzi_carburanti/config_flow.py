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
from .api import OsservaprezziAPI

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

    def __init__(self):
        """Initialize the flow."""
        self._search_data = {}
        self._found_stations = []

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Step iniziale: scelta metodo di configurazione."""
        if user_input is not None:
            if user_input["method"] == "search":
                return await self.async_step_region()
            return await self.async_step_manual()
        
        return self.async_show_menu(step_id="user", menu_options=["search", "manual"])

    async def async_step_search(self, user_input=None):
        """Alias per backward compatibility o direct call."""
        return await self.async_step_region()

    async def async_step_region(self, user_input: dict[str, Any] | None = None):
        """Scelta della regione."""
        session = async_get_clientsession(self.hass)
        api = OsservaprezziAPI(session)
        
        if user_input is not None:
            self._search_data["region"] = user_input["region"]
            return await self.async_step_province()

        regions = await api.get_regions()
        # regions is list of {id, description}
        options = {r["id"]: r.get("description", r.get("name")) for r in regions}
        # Sort by name
        sorted_options = dict(sorted(options.items(), key=lambda item: item[1]))

        return self.async_show_form(
            step_id="region",
            data_schema=vol.Schema({vol.Required("region"): vol.In(sorted_options)}),
        )

    async def async_step_province(self, user_input: dict[str, Any] | None = None):
        """Scelta della provincia."""
        session = async_get_clientsession(self.hass)
        api = OsservaprezziAPI(session)

        if user_input is not None:
            self._search_data["province"] = user_input["province"]
            return await self.async_step_town()

        region_id = self._search_data["region"]
        provinces = await api.get_provinces(region_id)
        options = {p["id"]: p.get("description", p.get("name")) for p in provinces}
        sorted_options = dict(sorted(options.items(), key=lambda item: item[1]))

        return self.async_show_form(
            step_id="province",
            data_schema=vol.Schema({vol.Required("province"): vol.In(sorted_options)}),
        )

    async def async_step_town(self, user_input: dict[str, Any] | None = None):
        """Scelta del comune."""
        session = async_get_clientsession(self.hass)
        api = OsservaprezziAPI(session)

        if user_input is not None:
            self._search_data["town"] = user_input["town"]
            return await self.async_step_select_station()

        province_id = self._search_data["province"]
        towns = await api.get_towns(province_id)
        options = {t["id"]: t.get("description", t.get("name")) for t in towns}
        sorted_options = dict(sorted(options.items(), key=lambda item: item[1]))

        return self.async_show_form(
            step_id="town",
            data_schema=vol.Schema({vol.Required("town"): vol.In(sorted_options)}),
        )

    async def async_step_select_station(self, user_input: dict[str, Any] | None = None):
        """Esegui ricerca ed elenca stazioni trovate per selezione multipla."""
        session = async_get_clientsession(self.hass)
        api = OsservaprezziAPI(session)
        errors = {}

        if user_input is not None:
            # user_input["stations"] è una lista di stringhe (che sono ID o combinazioni ID:Name)
            # Ma qui usiamo SelectSelector o MultiSelect con valori = ID come stringa
            selected_ids = user_input["stations"]
            
            # Recupera i dati completi dalle stazioni trovate in precedenza
            final_stations = []
            for s in self._found_stations:
                if str(s["id"]) in selected_ids:
                    final_stations.append({"id": s["id"], "name": s["name"]})
            
            # Crea config entry
            return self.async_create_entry(
                title=user_input.get("title", "Stazioni Osservaprezzi"),
                data={
                    "stations": final_stations,
                    "scan_interval": 3600
                }
            )

        # Esegui ricerca se non abbiamo ancora risultati o se è la prima volta in questo step
        if not self._found_stations:
            try:
                results = await api.search_by_area(
                    self._search_data["region"],
                    self._search_data["province"],
                    self._search_data["town"]
                )
                self._found_stations = results
            except Exception:
                errors["base"] = "search_failed"

        if not self._found_stations and not errors:
             errors["base"] = "no_stations_found"

        options = {}
        for s in self._found_stations:
             # Format: "Nome (Brand) - Indirizzo"
             brand = s.get("brand") or "Sconosciuto"
             addr = s.get("address") or ""
             label = f"{s['name']} ({brand})"
             if addr:
                 label += f" - {addr}"
             options[str(s["id"])] = label

        if not options:
            return self.async_abort(reason="no_stations_found")

        return self.async_show_form(
            step_id="select_station",
            data_schema=vol.Schema({
                vol.Required("stations"): verified_selector(options),
                vol.Optional("title", default=f"Stazioni {self._search_data.get('town_name', '')}"): str 
            }),
            errors=errors
        )

    async def async_step_manual(self, user_input: dict[str, Any] | None = None):
        """Passo manuale: accetta ID come testo multilinea (vecchio stile)."""
        errors: dict[str, str] = {}
        if user_input is None:
            data_schema = vol.Schema(
                {
                    vol.Required("stations", default="48524"): str,
                    vol.Optional("scan_interval", default=3600): int,
                    vol.Optional("title", default="Stazioni Osservaprezzi"): str,
                }
            )
            return self.async_show_form(
                step_id="manual",
                data_schema=data_schema,
                description_placeholders={"suggested_link": "https://carburanti.mise.gov.it/ospzSearch/zona"},
            )
        
        # ... logic as before ...
        stations_raw = user_input.get("stations", "")
        stations = _parse_stations_field(stations_raw)
        if not stations:
            errors["stations"] = "invalid_stations"

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
                            invalid_ids.append(sid)
                            continue
                        payload = await resp.json()
                        if not isinstance(payload, dict) or ("id" not in payload and "Id" not in payload):
                            invalid_ids.append(sid)
                            continue

                        preview_line, station_entry = build_station_preview(payload, sid, st.get("name"))
                        preview_lines.append(preview_line)
                        valid_stations.append(station_entry)
                except Exception:
                    invalid_ids.append(sid)

            if invalid_ids:
                invalid_list = ", ".join(str(i) for i in invalid_ids)
                self._valid_stations = valid_stations
                self._invalid_ids = invalid_ids
                self._pending_scan_interval = int(user_input.get("scan_interval") or 3600)
                self._pending_title = user_input.get("title") or "Stazioni Osservaprezzi"
                self._preview_text = "\n".join(preview_lines)

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
            return self.async_show_form(step_id="manual", data_schema=None, errors=errors)

        data = {
            "stations": stations,
            "scan_interval": int(user_input.get("scan_interval") or 3600),
            "title": user_input.get("title") or "Osservaprezzi stations",
        }
        
        if len(valid_stations) == 1:
            company = valid_stations[0].get("company")
            name = valid_stations[0].get("name")
            title = company or name or data["title"]
        else:
            title = data["title"]
        return self.async_create_entry(title=title, data=data)

def verified_selector(options):
    """Helper to create a multi-select selector."""
    from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig, SelectSelectorMode
    return SelectSelector(
        SelectSelectorConfig(
            options=[{"label": v, "value": k} for k, v in options.items()],
            multiple=True,
            mode=SelectSelectorMode.LIST,
        )
    )

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
        # Se viene creata una sola stazione valida, prediligi il company come titolo
        if len(stations) == 1:
            company = stations[0].get("company")
            name = stations[0].get("name")
            title = company or name or data["title"]
        else:
            title = data["title"]
        return self.async_create_entry(title=title, data=data)
