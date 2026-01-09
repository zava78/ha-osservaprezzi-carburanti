"""Utilità per l'integrazione osservaprezzi_carburanti.

Funzioni utili per costruire anteprime e ricavare coordinate dal payload delle API.
Queste funzioni sono scritte in modo puramente Python e sono testabili senza Home Assistant.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple


def find_coordinates(payload: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    """Cerca latitudine e longitudine nel payload.

    Supporta nomi di campo comuni usati da API diverse (lat, latitude, lng, longitude, ecc.).
    Restituisce una tupla (lat, lon) se trovate, altrimenti None.
    """
    lat_keys = ("lat", "latitude", "geoLat", "geolat")
    lon_keys = ("lon", "lng", "longitude", "geoLon", "geolon")
    lat = None
    lon = None
    for k in lat_keys:
        if k in payload and payload[k] is not None:
            try:
                lat = float(payload[k])
                break
            except Exception:
                continue
    for k in lon_keys:
        if k in payload and payload[k] is not None:
            try:
                lon = float(payload[k])
                break
            except Exception:
                continue
    if lat is not None and lon is not None:
        return lat, lon
    return None


def build_station_preview(payload: Dict[str, Any], sid: int, provided_name: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
    """Costruisce una riga di anteprima e un dizionario station_entry dal payload API.

    Ritorna (preview_line, station_entry) dove station_entry contiene almeno i campi
    `id` e `name` utilizzabili nella config entry.
    """
    name = payload.get("name") or payload.get("description") or provided_name or ""
    company = payload.get("company") or payload.get("gestore") or ""
    brand = payload.get("brand") or payload.get("brandName") or payload.get("marchio") or ""

    # Indirizzo: preferisci campo esplicito, altrimenti componi da componenti
    addr = payload.get("address") or payload.get("indirizzo") or payload.get("street")
    if not addr:
        parts = []
        for k in ("street", "civic", "city", "municipality", "prov", "province", "zip"):
            v = payload.get(k)
            if v:
                parts.append(str(v))
        addr = ", ".join(parts) if parts else ""

    coord = find_coordinates(payload)

    parts = [f"{sid}:", name]
    if company:
        parts.append(f"({company})")
    if brand:
        parts.append(f"brand={brand}")
    if addr:
        parts.append(f"addr={addr}")
    if coord:
        parts.append(f"coord={coord[0]:.6f},{coord[1]:.6f}")

    preview = " ".join(p for p in parts if p)

    station_entry = {"id": int(sid), "name": provided_name or name}
    return preview, station_entry
