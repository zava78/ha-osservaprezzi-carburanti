import os
import sys
import json
import importlib.util

# Load helpers.py by file path to avoid importing package __init__ (which requires Home Assistant)
helpers_path = os.path.join("custom_components", "osservaprezzi_carburanti", "helpers.py")
spec = importlib.util.spec_from_file_location("helpers_module", helpers_path)
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)
build_station_preview = helpers.build_station_preview

# Sample payload with company and coordinates
payload = {
    "id": 48524,
    "name": "Nome Distributore",
    "company": "Ener Coop",
    "brand": "BrandX",
    "address": "Via Roma 1",
    "lat": 45.123456,
    "lon": 9.123456,
}

preview, entry = build_station_preview(payload, 48524, None)
print("preview:", preview)
print("entry:", entry)
print("company in entry:", entry.get("company"))

# Verify translations are in Italian and contain expected keys
tpath = os.path.join("custom_components", "osservaprezzi_carburanti", "translations", "it.json")
with open(tpath, "r", encoding="utf-8") as f:
    t = json.load(f)

u_title = t.get("config", {}).get("step", {}).get("user", {}).get("title")
print("config.user.title:", u_title)
print("is Italian (contains 'Configura'):", isinstance(u_title, str) and "Configura" in u_title)

# Check description placeholder exists
u_desc = t.get("config", {}).get("step", {}).get("user", {}).get("description")
print("description contains suggested link placeholder:", "suggested_link" in (u_desc or ""))
