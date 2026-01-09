# ha-osservaprezzi-carburanti

[![Python tests](https://github.com/zava78/ha-osservaprezzi-carburanti/actions/workflows/python-tests.yml/badge.svg)](https://github.com/zava78/ha-osservaprezzi-carburanti/actions)
[![Release](https://img.shields.io/github/v/release/zava78/ha-osservaprezzi-carburanti?label=release)](https://github.com/zava78/ha-osservaprezzi-carburanti/releases)
[![HACS](https://img.shields.io/badge/HACS-custom-brightgreen.svg)](https://hacs.xyz/)
[![Coverage](https://img.shields.io/codecov/c/github/zava78/ha-osservaprezzi-carburanti?logo=codecov)](https://codecov.io/gh/zava78/ha-osservaprezzi-carburanti)

Home Assistant custom integration to read petrol station / service area prices from the Italian "Osservaprezzi Carburanti" (MIMIT).

Features

- Create sensors per station and per fuel (self / attended) using station ID from Osservaprezzi
- Uses Home Assistant DataUpdateCoordinator for efficient polling
- Provides station metadata and fuel attributes, brand logo placeholder support

Quick install (HACS or manual)

Manual (development / local):

- Copy the `custom_components/osservaprezzi_carburanti` folder into your HA `config` directory.
- Restart Home Assistant.

YAML configuration example (put in `configuration.yaml`):

```yaml
osservaprezzi_carburanti:
  scan_interval: 7200 # seconds, default 3600
  stations:
    - id: 48524
      name: "Distributore Ener Coop Borgo Virgilio"
    - id: 14922
      name: "Service Area Esempio A1 Nord"
```

Entity naming

- `sensor.<configured-or-api-name>_<fuel>_<self|attended>`
- `sensor.osservaprezzi_<id>_meta` contains station metadata as attributes.

Lovelace demo card

You can add a simple demo card that shows the station logo, fuel type, current price and a 14-day price history chart using Home Assistant history.

1. Add the resource in Lovelace (Resources) or via YAML pointing to this file:

```
/local/custom_components/osservaprezzi_carburanti/www/osservaprezzi-card.js
```

2. Example card configuration:

```yaml
type: 'custom:osservaprezzi-card'
entity: sensor.osservaprezzi_48524_benzina_self
fuel: Benzina
logo: /local/custom_components/osservaprezzi_carburanti/assets/brands/eni.png
```

Notes:
- The card uses Home Assistant's `history/period` websocket API to fetch the last 14 days of the selected entity's states — ensure Home Assistant history recorder is enabled for the entity to see the graph.
- Chart is rendered with Chart.js loaded from CDN.

Attributes exposed (fuel sensors)

- `fuel_name`, `is_self`, `brand`, `company`, `name`, `address`, `validity_date`, `brand_logo`, `raw_fuel`

Brand logos

- Place PNG files in `custom_components/osservaprezzi_carburanti/assets/brands/`.
- Filenames should match the keys in `BRAND_LOGOS` mapping (see `const.py`).

Generating demo placeholder logos

A small script is provided to generate demo placeholder PNG logos (1x1 transparent)
for the known brand filenames. Run this from the project root with Python:

```powershell
python .\tools\generate_brand_placeholders.py
```

Replace the generated files in `custom_components/osservaprezzi_carburanti/assets/brands/` with real PNGs when available.

How to find station ID

- Use the Osservaprezzi search page: https://carburanti.mise.gov.it/ospzSearch/zona
- Inspect the API endpoint for a station, URL contains the ID, e.g. `.../servicearea/14922`.

Publishing to GitHub and HACS

1. Create a new repository named `ha-osservaprezzi-carburanti` under your `zava78` account.
2. Initialize the repo locally and push the files.

Suggested commands (PowerShell):

```powershell
cd "C:\path\to\your\project\folder"
git init
git remote add origin https://github.com/zava78/ha-osservaprezzi-carburanti.git
git add .
git commit -m "Initial import of ha-osservaprezzi-carburanti"
git branch -M main
git push -u origin main
```

To add to HACS as a custom repository:

- In HACS -> Integrations -> three dots -> Custom repositories -> add the GitHub repo URL and select `integration`.

Roadmap / Ideas

- Add a Config Flow UI to manage station IDs from the Integrations page
- Add per-fuel sensors with history/stats
- Improve brand logo matching and provide high-quality PNGs

License: MIT

Config Flow (UI)

This integration also provides a Config Flow so you can add stations from the Integrations UI.
During the flow you can provide multiple stations at once by entering one station per line in the
form field. Each line can be either the numeric station id, or `id,name` (comma or semicolon separated).

Example lines for the form:

```
48524,Distributore Ener Coop Borgo Virgilio
14922;Service Area Esempio A1 Nord
```

The flow will create one config entry containing all provided stations; each station will expose
its sensors under that entry.

**Gestione delle entità e dispositivi (User friendly)**

- **Ogni distributore configurato tramite l'interfaccia (Config Entry) è esposto come un singolo dispositivo** in Home Assistant. I sensori dei carburanti (self/servito) vengono creati come entità figlie di quel dispositivo — questo permette di:
  - Disabilitare o rinominare facilmente tutte le entità di un distributore dal pannello "Dispositivi" → seleziona il distributore → gestione entità.
  - Vedere chiaramente quale configurazione (entry) ha creato il dispositivo, evitando collisioni quando lo stesso distributore è aggiunto più volte in diverse integrazioni/istanze.

- **Unique IDs e DeviceInfo:** le entità generate includono l'`entry_id` della configurazione nel `unique_id` e negli `identifiers` del `DeviceInfo` quando l'entità è creata da una Config Entry. Questo significa che:
  - Lo stesso distributore aggiunto due volte in due entry distinte apparirà come due dispositivi separati (ognuno con le proprie entità), permettendoti di gestirli indipendentemente.
  - Se usi la configurazione YAML, il comportamento resta invariato (le entità non avranno `entry_id` nello unique_id).

- **Disabilitare singole entità:** per rimuovere temporaneamente una singola lettura (ad esempio un tipo di carburante che non ti interessa), vai su `Impostazioni -> Dispositivi ed entità -> Entità`, cerca la `sensor.<nome>` desiderata e scegli `Disabilita`. Le entità non saranno rimosse dalla configurazione ma non invieranno stati finché disabilitate.

- **Icona del componente:** le entità usano una icona predefinita `mdi:fuel` (puoi cambiarla dalle impostazioni dell'entità se preferisci un'icona diversa).

Se vuoi, posso aggiungere una sezione con immagini schermate (screenshot) che mostrano i passaggi per disabilitare/rinominare entità in Home Assistant.
