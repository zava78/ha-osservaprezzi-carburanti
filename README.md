## Lovelace demo card

You can add a simple demo card that shows the station logo, fuel type, current price and a 14-day price history chart using Home Assistant history.
### Card di confronto (più stazioni)

Questa card confronta lo stesso tipo di carburante su più stazioni, mostrando i prezzi correnti affiancati e un grafico con le serie storiche (ultimi 14 giorni).
Posiziona il file `osservaprezzi-compare-card.js` in `www/` come per la card singola, quindi aggiungi la risorsa in Lovelace.

Esempio di configurazione:

```yaml
type: 'custom:osservaprezzi-compare-card'
title: 'Confronto Benzina'
fuel: 'Benzina'
entities:
  - sensor.osservaprezzi_48524_benzina_self
  - sensor.osservaprezzi_14922_benzina_self
  - sensor.osservaprezzi_12345_benzina_self
# opzionale: array parallelo di paths per i loghi
logos:
  - /local/custom_components/osservaprezzi_carburanti/assets/brands/eni.png
  - /local/custom_components/osservaprezzi_carburanti/assets/brands/ip.png
  - /local/custom_components/osservaprezzi_carburanti/assets/brands/q8.png
```

Note:
- La card richiede almeno 2 entità nella lista `entities`.
- Per vedere il grafico è necessario che l'`history recorder` registri gli stati delle entità.
- Le serie del grafico vengono richieste in un'unica chiamata `history/period` per tutte le entità fornite.
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
# ha-osservaprezzi-carburanti

[![Python tests](https://github.com/zava78/ha-osservaprezzi-carburanti/actions/workflows/python-tests.yml/badge.svg)](https://github.com/zava78/ha-osservaprezzi-carburanti/actions)
[![Release](https://img.shields.io/github/v/release/zava78/ha-osservaprezzi-carburanti?label=release)](https://github.com/zava78/ha-osservaprezzi-carburanti/releases)
[![HACS](https://img.shields.io/badge/HACS-custom-brightgreen.svg)](https://hacs.xyz/)
[![Coverage](https://img.shields.io/codecov/c/github/zava78/ha-osservaprezzi-carburanti?logo=codecov)](https://codecov.io/gh/zava78/ha-osservaprezzi-carburanti)

Integrazione custom per Home Assistant che legge i prezzi dei distributori/aree di servizio dall'API pubblica italiana "Osservaprezzi Carburanti" (MIMIT).

## Caratteristiche principali

- Crea sensori per ogni impianto e per ogni tipo di carburante (self / servito) usando l'ID dell'impianto fornito da Osservaprezzi
- Usa `DataUpdateCoordinator` di Home Assistant per un polling efficiente
- Espone metadati dell'impianto e attributi del carburante; supporto per loghi brand in `assets/brands/`
- Flow di configurazione (Config Flow) con anteprima e possibilità di inserire più impianti in una sola entry

## Installazione rapida (HACS o manuale)

Manuale (sviluppo / locale):

- Copia la cartella `custom_components/osservaprezzi_carburanti` nella directory `config` di Home Assistant.
- Riavvia Home Assistant.

## Esempio configurazione YAML (opzionale, `configuration.yaml`):

```yaml
osservaprezzi_carburanti:
  scan_interval: 7200 # secondi, default 3600
  stations:
    - id: 48524
      name: "Distributore Ener Coop Borgo Virgilio"
    - id: 14922
      name: "Service Area Esempio A1 Nord"
```

## Nomi delle entità

- `sensor.<nome-configurato-o-API>_<carburante>_<self|attended>`
- `sensor.osservaprezzi_<id>_meta` contiene i metadati dell'impianto negli attributi

## Card Lovelace

Sono fornite due card demo nella cartella `www/`:

- `osservaprezzi-card.js` — card singola che mostra logo, carburante, prezzo corrente e grafico 14 giorni per un'entità.
- `osservaprezzi-compare-card.js` — card di confronto che mostra prezzi correnti affiancati per più stazioni e un grafico multi-linea con le serie storiche.

### Esempio card singola:

```yaml
type: 'custom:osservaprezzi-card'
entity: sensor.osservaprezzi_48524_benzina_self
fuel: Benzina
logo: /local/custom_components/osservaprezzi_carburanti/assets/brands/eni.png
```

### Esempio card confronto:

```yaml
type: 'custom:osservaprezzi-compare-card'
title: 'Confronto Benzina'
fuel: 'Benzina'
entities:
  - sensor.osservaprezzi_48524_benzina_self
  - sensor.osservaprezzi_14922_benzina_self
  - sensor.osservaprezzi_12345_benzina_self
# opzionale: array parallelo di path per i loghi
logos:
  - /local/custom_components/osservaprezzi_carburanti/assets/brands/eni.png
  - /local/custom_components/osservaprezzi_carburanti/assets/brands/ip.png
  - /local/custom_components/osservaprezzi_carburanti/assets/brands/q8.png
```

### Note sulle card:

- Le card richiedono che le risorse JS siano aggiunte come risorsa in Lovelace (HACS può aiutare con questa operazione se il repository è installato via HACS).
- Per il grafico è necessario che l'`history recorder` registri gli stati delle entità interessate.
- La card di confronto ordina la tabella per prezzo (dal più basso) e evidenzia il prezzo migliore.

## Attributi esposti (sensori carburante)

- `fuel_name`, `is_self`, `brand`, `company`, `name`, `address`, `validity_date`, `brand_logo`, `raw_fuel`

## Loghi brand

- Posiziona i file PNG in `custom_components/osservaprezzi_carburanti/assets/brands/`.
- I nomi file devono corrispondere alle chiavi mappate in `BRAND_LOGOS` (vedi `custom_components/osservaprezzi_carburanti/const.py`).

## Generazione loghi demo

Uno script `tools/generate_brand_placeholders.py` è fornito per generare loghi placeholder (PNG 1x1 trasparenti) che puoi sostituire con immagini reali.

```powershell
python .\tools\generate_brand_placeholders.py
```

## Come trovare l'ID di un impianto

- Usa la pagina di ricerca Osservaprezzi: https://carburanti.mise.gov.it/ospzSearch/zona
- Apri la richiesta API e cerca l'URL `/servicearea/<ID>` per trovare l'ID numerico.

## Pubblicazione su GitHub e HACS

1. Crea un repository GitHub denominato `ha-osservaprezzi-carburanti` sotto il tuo account `zava78` (se non lo hai già fatto).
2. Spingi il codice locale sul repository remoto e aggiungi l'integrazione a HACS come repository personalizzato (Integration).

Comandi suggeriti (PowerShell):

```powershell
cd "C:\path\to\your\project\folder"
git init
git remote add origin https://github.com/zava78/ha-osservaprezzi-carburanti.git
git add .
git commit -m "Initial import of ha-osservaprezzi-carburanti"
git branch -M main
git push -u origin main
```

Per aggiungere il repository a HACS:

- In HACS -> Integrations -> tre punti -> Custom repositories -> incolla l'URL del repo e seleziona `integration`.

## Roadmap / Idee

- Migliorare il matching dei loghi dei brand e aggiungere PNG ad alta qualità
- Aggiungere più test automatici e job di lint in CI
- Aggiungere screenshot e guida passo-passo nella documentazione

Licenza: MIT

## Flow di configurazione (Config Flow)

L'integrazione fornisce anche un Config Flow per aggiungere gli impianti dall'interfaccia "Integrazioni".
Nel form puoi inserire più impianti separandoli con righe distinte; ogni riga può essere solo l'ID numerico oppure `id,name` (separato da virgola o punto e virgola).

Esempio di righe accettate nel form:

```
48524,Distributore Ener Coop Borgo Virgilio
14922;Service Area Esempio A1 Nord
```

Quando completi il flow viene creata una singola config entry contenente tutti gli impianti inseriti; ogni impianto esporrà i propri sensori sotto quella entry.

## Gestione entità e dispositivi

- Ogni distributore aggiunto tramite Config Entry è esposto come dispositivo in Home Assistant; i sensori carburante sono entità figlie del dispositivo.
- Le entità create da una Config Entry includono l'`entry_id` nel `unique_id` e negli `identifiers` del `DeviceInfo`, quindi lo stesso distributore aggiunto in due entry diverse apparirà come due dispositivi distinti (evitando collisioni).
- Se usi YAML, il comportamento rimane invariato: le entità non avranno `entry_id` nello `unique_id`.

Se vuoi, posso aggiungere screenshot o ulteriori esempi di automazioni che sfruttano questi sensori.
