"""API Client for Osservaprezzi Carburanti."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import aiohttp

from .const import (
    API_BRAND_LOGOS_URL,
    API_SEARCH_AREA_URL,
    API_URL_TEMPLATE,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class OsservaprezziAPI:
    """Client for Osservaprezzi API."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        """Initialize the API client."""
        self.session = session

    async def get_station_details(self, station_id: int) -> Dict[str, Any]:
        """Fetch details and prices for a specific station."""
        url = API_URL_TEMPLATE.format(id=station_id)
        async with self.session.get(url, timeout=REQUEST_TIMEOUT) as resp:
            if resp.status != 200:
                text = await resp.text()
                raise Exception(f"Error fetching station {station_id}: HTTP {resp.status} - {text}")
            
            data = await resp.json()
            if not isinstance(data, dict):
                raise Exception(f"Unexpected data format for station {station_id}")
            
            return data

    async def get_all_logos(self) -> Dict[str | int, str]:
        """Fetch all brand logos and return a map of Brand ID/Name -> Base64 Image."""
        try:
            async with self.session.get(API_BRAND_LOGOS_URL, timeout=REQUEST_TIMEOUT) as resp:
                if resp.status != 200:
                    _LOGGER.warning("Failed to fetch brand logos: HTTP %s", resp.status)
                    return {}
                
                payload = await resp.json()
                # Structure: { "loghi": [ { "bandieraId": 123, "bandiera": "Name", "logoMarkerList": [...] }, ... ] }
                if not isinstance(payload, dict):
                    return {}
                
                data = payload.get("loghi")
                if not isinstance(data, list):
                    return {}
                
                logos_map: Dict[str | int, str] = {}
                for item in data:
                    brand_id = item.get("bandieraId")
                    brand_name = item.get("bandiera")
                    
                    # logoMarkerList is a list of logo objects
                    markers = item.get("logoMarkerList")
                    if isinstance(markers, list) and markers:
                        # Pick the first one
                        logo_obj = markers[0]
                        content = logo_obj.get("content")
                        ext = logo_obj.get("estensione", "png")
                        
                        if content:
                            if not content.startswith("data:"):
                                content = f"data:image/{ext};base64,{content}"
                            
                            # Map by ID
                            if brand_id:
                                logos_map[brand_id] = content
                                logos_map[str(brand_id)] = content
                            
                            # Map by Name
                            if brand_name:
                                logos_map[brand_name] = content
                                # Also key by normalized/lowercase just in case
                                logos_map[brand_name.lower()] = content

                return logos_map
        except Exception as err:
            _LOGGER.warning("Error fetching brand logos: %s", err)
            return {}

    async def get_regions(self) -> List[Dict[str, Any]]:
        """Fetch list of regions."""
        url = "https://carburanti.mise.gov.it/ospzApi/registry/region"
        try:
            async with self.session.get(url, timeout=REQUEST_TIMEOUT) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return data.get("results", [])
        except Exception:
            return []

    async def get_provinces(self, region_id: int) -> List[Dict[str, Any]]:
        """Fetch list of provinces for a region."""
        url = "https://carburanti.mise.gov.it/ospzApi/registry/province"
        params = {"regionId": region_id}
        try:
            async with self.session.get(url, params=params, timeout=REQUEST_TIMEOUT) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return data.get("results", [])
        except Exception:
            return []

    async def get_towns(self, province_id: str) -> List[Dict[str, Any]]:
        """Fetch list of towns for a province."""
        url = "https://carburanti.mise.gov.it/ospzApi/registry/town"
        params = {"province": province_id}
        try:
            async with self.session.get(url, params=params, timeout=REQUEST_TIMEOUT) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
                return data.get("results", [])
        except Exception:
            return []

    async def search_by_area(self, region_id: int, province_id: str, town_id: str) -> List[Dict[str, Any]]:
        """Search stations by geographical area (Regione -> Provincia -> Comune)."""
        payload = {
            "region": region_id,
            "province": province_id,
            "town": town_id,
        }
        try:
            async with self.session.post(API_SEARCH_AREA_URL, json=payload, timeout=REQUEST_TIMEOUT) as resp:
                resp.raise_for_status()
                data = await resp.json()
                # API usually returns a list of stations directly or wrapped
                if isinstance(data, list):
                    return data
                return data.get("results", [])
        except Exception as err:
            _LOGGER.error("Search failed for area %s-%s-%s: %s", region_id, province_id, town_id, err)
            raise
