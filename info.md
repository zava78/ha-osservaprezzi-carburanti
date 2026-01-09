# ha-osservaprezzi-carburanti

This repository contains a Home Assistant custom integration to fetch fuel prices from the Italian Osservaprezzi (MIMIT) API.

This integration can be installed via HACS (preferred) or manually by copying the `custom_components/osservaprezzi_carburanti` folder into your Home Assistant configuration directory.

Summary
- Sensors per impianto e per carburante (self/attended)
- DataUpdateCoordinator per polling efficiente
- Config Flow con validazione live e preview dettagliata

Installation
- HACS: add this repo as a Custom Repository (category "integration") and install from HACS -> Integrations.
- Manual: copy `custom_components/osservaprezzi_carburanti` into `<config>/custom_components/` and restart Home Assistant.

Quick troubleshooting
- If entities are `unavailable`, controlla i log di Home Assistant per errori di rete e verifica l'ID impianto.

Contributing
- Esegui i test locali prima di aprire una PR: `python .\tools\run_preview_tests.py`.

License: MIT
