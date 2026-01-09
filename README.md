![Logo](images/logo.png)

# ha-osservaprezzi-carburanti

[![Release](https://img.shields.io/github/v/release/zava78/ha-osservaprezzi-carburanti?label=release)](https://github.com/zava78/ha-osservaprezzi-carburanti/releases)
[![HACS](https://img.shields.io/badge/HACS-custom-brightgreen.svg)](https://hacs.xyz/)
[![Coverage](https://img.shields.io/codecov/c/github/zava78/ha-osservaprezzi-carburanti?logo=codecov)](https://codecov.io/gh/zava78/ha-osservaprezzi-carburanti)

Integrazione custom per Home Assistant che legge i prezzi dei distributori/aree
di servizio dall'API pubblica italiana "Osservaprezzi Carburanti" (MIMIT).

Nota: per cercare gli impianti e ottenere gli ID usa il sito del Ministero: https://carburanti.mise.gov.it/ospzSearch/zona

## Caratteristiche principali

- Crea sensori per ogni impianto e per ogni tipo di carburante (self / servito)
  usando l'ID dell'impianto fornito da Osservaprezzi.
- Usa `DataUpdateCoordinator` di Home Assistant per un polling efficiente.
- Espone metadati dell'impianto e attributi del carburante; supporto per
  loghi dei brand in `assets/brands/`.
- Flow di configurazione (Config Flow) con anteprima e possibilità di inserire
  più impianti in una singola config entry.

## Installazione rapida (HACS)

L'integrazione può essere installata tramite HACS. Dopo l'installazione, riavvia Home Assistant.

La configurazione degli impianti avviene tramite l'interfaccia (Config Flow) — non è
più necessario aggiungere manualmente ID o blocchi YAML: usa l'interfaccia
"Integrazioni" → "Aggiungi Integrazione" e cerca "Osservaprezzi Carburanti".

## Nomi delle entità

- `sensor.<nome-configurato-o-API>_<carburante>_<self|attended>`
- `sensor.osservaprezzi_<id>_meta` contiene i metadati dell'impianto negli attributi.

Le entità e i dispositivi vengono creati automaticamente quando aggiungi gli impianti
tramite il Config Flow. Se aggiungi una singola stazione, il titolo della Config Entry
viene impostato automaticamente sul campo `company` (se presente nell'API) o sul nome
della stazione.

## Card Lovelace

- `osservaprezzi-card.js` — card singola che mostra logo, carburante, prezzo
  corrente e grafico 14 giorni per un'entità.
- `osservaprezzi-compare-card.js` — card di confronto che mostra prezzi
  correnti e un grafico multi-linea per più stazioni.

### Esempio card singola

```yaml
type: "custom:osservaprezzi-card"
entity: sensor.osservaprezzi_48524_benzina_self
fuel: Benzina
logo: /local/custom_components/osservaprezzi_carburanti/assets/brands/eni.png
```

### Esempio card confronto

```yaml
type: "custom:osservaprezzi-compare-card"
title: "Confronto Benzina"
fuel: "Benzina"
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

### Note sulle card

- Le risorse JS devono essere aggiunte come risorsa in Lovelace (HACS può
  semplificare questa operazione se il repository è installato via HACS).
- Per il grafico è necessario che l'`history recorder` registri gli stati delle
  entità interessate.
- La card di confronto ordina la tabella per prezzo (dal più basso) ed
  evidenzia il prezzo migliore.

## Attributi esposti (sensori carburante)

- `fuel_name`, `is_self`, `brand`, `company`, `name`, `address`, `validity_date`, `brand_logo`, `raw_fuel`

## Loghi brand

- Posiziona i file PNG in `custom_components/osservaprezzi_carburanti/assets/brands/`.
- I nomi file devono corrispondere alle chiavi mappate in `BRAND_LOGOS` (vedi
  `custom_components/osservaprezzi_carburanti/const.py`).

## Generazione loghi demo

Uno script `tools/generate_brand_placeholders.py` è fornito per generare loghi
placeholder (PNG 1x1 trasparenti) che puoi sostituire con immagini reali.

```powershell
python .\tools\generate_brand_placeholders.py
```

## Come trovare l'ID di un impianto

- Usa la pagina di ricerca Osservaprezzi: https://carburanti.mise.gov.it/ospzSearch/zona
- Apri la richiesta API e cerca l'URL `/servicearea/<ID>` per trovare l'ID numerico.

## Pubblicazione su GitHub e HACS

1. Crea un repository GitHub denominato `ha-osservaprezzi-carburanti` sotto il
   tuo account `zava78` (se non lo hai già fatto).
2. Spingi il codice locale sul repository remoto e aggiungi l'integrazione a
   HACS come repository personalizzato (Integration).

Comandi suggeriti (PowerShell):

```powershell
cd "C:\path\to\your\project\folder"
git init
git remote add origin https://github.com/zava78/ha-osservaprezzi-carburanti.git
git add .
git commit -m "Import iniziale di ha-osservaprezzi-carburanti"
git branch -M main
git push -u origin main
```

Per aggiungere il repository a HACS:

- In HACS -> Integrations -> tre punti -> Custom repositories -> incolla l'URL
  del repo e seleziona `integration`.

## Roadmap / Idee

- Migliorare il matching dei loghi dei brand e aggiungere PNG ad alta qualità
- Aggiungere più test automatici e job di lint in CI
- Aggiungere screenshot e guida passo-passo nella documentazione

## Licenza

- Questo progetto è rilasciato sotto Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0).
- URL della licenza: https://creativecommons.org/licenses/by-nc-sa/4.0/

Nota: la licenza CC BY-NC-SA permette la condivisione e l'adattamento del
materiale a condizione di attribuire l'autore, non utilizzarlo per scopi
commerciali e distribuire le opere derivate con la stessa licenza.

## Flow di configurazione (Config Flow)

L'integrazione fornisce un Config Flow per aggiungere gli impianti dall'interfaccia
"Integrazioni" → "Aggiungi Integrazione" → cerca "Osservaprezzi Carburanti".

Nel form puoi inserire più impianti separandoli con righe distinte; ogni riga può
essere solo l'ID numerico oppure `id,name` (separato da virgola o punto e virgola).

Esempio di righe accettate nel form:

```
48524,Distributore Ener Coop Borgo Virgilio
14922;Service Area Esempio A1 Nord
```

Quando completi il flow viene creata una singola Config Entry contenente tutti
gli impianti inseriti; ogni impianto esporrà i propri sensori e dispositivi sotto
quella entry. Il processo è completamente automatico: non sono richieste
modifiche manuali a `configuration.yaml`.

## Gestione entità e dispositivi

- Ogni distributore aggiunto tramite Config Entry è esposto come dispositivo in
  Home Assistant; i sensori carburante sono entità figlie del dispositivo.
- Le entità create da una Config Entry includono l'`entry_id` nel `unique_id`
  e negli `identifiers` del `DeviceInfo`, quindi lo stesso distributore aggiunto
  in due entry diverse apparirà come due dispositivi distinti (evitando
  collisioni).
- Se usi YAML, il comportamento rimane invariato: le entità non avranno
  `entry_id` nello `unique_id`.

Se vuoi, posso aggiungere screenshot o ulteriori esempi di automazioni che
sfruttano questi sensori.

## Lovelace: card di esempio

````markdown
# ha-osservaprezzi-carburanti

[![Release](https://img.shields.io/github/v/release/zava78/ha-osservaprezzi-carburanti?label=release)](https://github.com/zava78/ha-osservaprezzi-carburanti/releases)
[![HACS](https://img.shields.io/badge/HACS-custom-brightgreen.svg)](https://hacs.xyz/)
[![Coverage](https://img.shields.io/codecov/c/github/zava78/ha-osservaprezzi-carburanti?logo=codecov)](https://codecov.io/gh/zava78/ha-osservaprezzi-carburanti)

Integrazione custom per Home Assistant che legge i prezzi dei distributori/aree
di servizio dall'API pubblica italiana "Osservaprezzi Carburanti" (MIMIT).

Nota: per cercare gli impianti e ottenere gli ID usa il sito del Ministero: https://carburanti.mise.gov.it/ospzSearch/zona

## Caratteristiche principali

- Crea sensori per ogni impianto e per ogni tipo di carburante (self / servito)
  usando l'ID dell'impianto fornito da Osservaprezzi.
- Usa `DataUpdateCoordinator` di Home Assistant per un polling efficiente.
- Espone metadati dell'impianto e attributi del carburante; supporto per
  loghi dei brand in `assets/brands/`.
- Flow di configurazione (Config Flow) con anteprima e possibilità di inserire
  più impianti in una singola config entry.

## Installazione rapida (HACS)

L'integrazione può essere installata tramite HACS o semplicemente copiando la cartella
`custom_components/osservaprezzi_carburanti` nella directory `config` di Home Assistant
se stai lavorando in locale. Dopo l'installazione, riavvia Home Assistant.

La configurazione degli impianti avviene tramite l'interfaccia (Config Flow) — non è
più necessario aggiungere manualmente ID o blocchi YAML: usa l'interfaccia
"Integrazioni" → "Aggiungi Integrazione" e cerca "Osservaprezzi Carburanti".

## Nomi delle entità

- `sensor.<nome-configurato-o-API>_<carburante>_<self|attended>`
- `sensor.osservaprezzi_<id>_meta` contiene i metadati dell'impianto negli attributi.

Le entità e i dispositivi vengono creati automaticamente quando aggiungi gli impianti
tramite il Config Flow. Se aggiungi una singola stazione, il titolo della Config Entry
viene impostato automaticamente sul campo `company` (se presente nell'API) o sul nome
della stazione.

## Card Lovelace

- `osservaprezzi-card.js` — card singola che mostra logo, carburante, prezzo
  corrente e grafico 14 giorni per un'entità.
- `osservaprezzi-compare-card.js` — card di confronto che mostra prezzi
  correnti e un grafico multi-linea per più stazioni.

### Esempio card singola:

````yaml
type: "custom:osservaprezzi-card"
entity: sensor.osservaprezzi_48524_benzina_self
```markdown
# ha-osservaprezzi-carburanti
  `custom_components/osservaprezzi_carburanti/const.py`).

## Generazione loghi demo

Uno script `tools/generate_brand_placeholders.py` è fornito per generare loghi
placeholder (PNG 1x1 trasparenti) che puoi sostituire con immagini reali.

```powershell
python .\tools\generate_brand_placeholders.py
````

## Come trovare l'ID di un impianto

- Usa la pagina di ricerca Osservaprezzi: https://carburanti.mise.gov.it/ospzSearch/zona
- Apri la richiesta API e cerca l'URL `/servicearea/<ID>` per trovare l'ID numerico.

## Pubblicazione su GitHub e HACS

1. Crea un repository GitHub denominato `ha-osservaprezzi-carburanti` sotto il
   tuo account `zava78` (se non lo hai già fatto).
2. Spingi il codice locale sul repository remoto e aggiungi l'integrazione a
   HACS come repository personalizzato (Integration).

Comandi suggeriti (PowerShell):

```powershell
cd "C:\path\to\your\project\folder"
git init
git remote add origin https://github.com/zava78/ha-osservaprezzi-carburanti.git
git add .
git commit -m "Import iniziale di ha-osservaprezzi-carburanti"
git branch -M main
git push -u origin main
```

Per aggiungere il repository a HACS:

- In HACS -> Integrations -> tre punti -> Custom repositories -> incolla l'URL
  del repo e seleziona `integration`.

## Roadmap / Idee

- Migliorare il matching dei loghi dei brand e aggiungere PNG ad alta qualità
- Aggiungere più test automatici e job di lint in CI
- Aggiungere screenshot e guida passo-passo nella documentazione

Licenza

- Questo progetto è rilasciato sotto Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0).
- URL della licenza: https://creativecommons.org/licenses/by-nc-sa/4.0/

Nota: la licenza CC BY-NC-SA permette la condivisione e l'adattamento del
materiale a condizione di attribuire l'autore, non utilizzarlo per scopi
commerciali e distribuire le opere derivate con la stessa licenza.

## Flow di configurazione (Config Flow)

L'integrazione fornisce un Config Flow per aggiungere gli impianti dall'interfaccia
"Integrazioni" → "Aggiungi Integrazione" → cerca "Osservaprezzi Carburanti".

Nel form puoi inserire più impianti separandoli con righe distinte; ogni riga può
essere solo l'ID numerico oppure `id,name` (separato da virgola o punto e virgola).

Esempio di righe accettate nel form:

```
48524,Distributore Ener Coop Borgo Virgilio
14922;Service Area Esempio A1 Nord
```

Quando completi il flow viene creata una singola Config Entry contenente tutti
gli impianti inseriti; ogni impianto esporrà i propri sensori e dispositivi sotto
quella entry. Il processo è completamente automatico: non sono richieste
modifiche manuali a `configuration.yaml`.

## Gestione entità e dispositivi

- Ogni distributore aggiunto tramite Config Entry è esposto come dispositivo in
  Home Assistant; i sensori carburante sono entità figlie del dispositivo.
- Le entità create da una Config Entry includono l'`entry_id` nel `unique_id`
  e negli `identifiers` del `DeviceInfo`, quindi lo stesso distributore aggiunto
  in due entry diverse apparirà come due dispositivi distinti (evitando
  collisioni).
- Se usi YAML, il comportamento rimane invariato: le entità non avranno
  `entry_id` nello `unique_id`.

Se vuoi, posso aggiungere screenshot o ulteriori esempi di automazioni che
sfruttano questi sensori.
````
