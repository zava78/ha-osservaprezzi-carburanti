class OsservaprezziCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) return;
    this._update();
  }

  connectedCallback() {
    if (this._initialized) return;
    this._shadow = this.attachShadow({ mode: 'open' });
    this._container = document.createElement('div');
    this._container.className = 'os-card';
    const style = document.createElement('style');
    style.textContent = `
      .os-card { font-family: sans-serif; border: 1px solid var(--card-border-color, #ddd); border-radius: 8px; padding: 12px; background: var(--card-background, #fff); }
      .os-header { display:flex; align-items:center; gap:12px }
      .os-logo { width:48px; height:48px; object-fit:contain }
      .os-title { font-size: 1.0rem; font-weight:600 }
      .os-sub { color: var(--secondary-text-color, #666); font-size:0.9rem }
      .os-price { font-size:1.4rem; font-weight:700; margin-top:6px }
      canvas { width:100%; height:120px }
    `;
    this._shadow.appendChild(style);
    this._shadow.appendChild(this._container);

    // intestazione
    this._header = document.createElement('div');
    this._header.className = 'os-header';
    this._logo = document.createElement('img');
    this._logo.className = 'os-logo';
    this._header.appendChild(this._logo);
    this._titleWrap = document.createElement('div');
    this._title = document.createElement('div');
    this._title.className = 'os-title';
    this._sub = document.createElement('div');
    this._sub.className = 'os-sub';
    this._titleWrap.appendChild(this._title);
    this._titleWrap.appendChild(this._sub);
    this._header.appendChild(this._titleWrap);
    this._container.appendChild(this._header);

    // prezzo
    this._priceEl = document.createElement('div');
    this._priceEl.className = 'os-price';
    this._container.appendChild(this._priceEl);

    // grafico
    this._canvas = document.createElement('canvas');
    this._container.appendChild(this._canvas);

    this._initialized = true;
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error('Devi definire un\'entità nel campo `entity` della configurazione');
    }
    this._config = config;
  }

  _update() {
    const entityId = this._config.entity;
    const entity = this._hass.states[entityId];
    const fuel = this._config.fuel || (entity && entity.attributes && entity.attributes.fuel_name) || '';
    const logo = this._config.logo || (entity && entity.attributes && entity.attributes.brand_logo) || '';
    const name = (entity && entity.attributes && entity.attributes.name) || entityId;
    const price = entity ? entity.state : 'unavailable';

    // aggiorna intestazione
    if (logo) {
      // logo may be a local path like /local/...
      this._logo.src = logo;
      this._logo.style.display = '';
    } else {
      this._logo.style.display = 'none';
    }
    this._title.textContent = name;
    this._sub.textContent = fuel;

    // aggiorna prezzo
    this._priceEl.textContent = price && price !== 'unknown' ? `${price} €/l` : 'n/a';

    // recupera lo storico degli ultimi 14 giorni e disegna il grafico
    this._drawHistory(entityId);
  }

  async _drawHistory(entityId) {
    // compute start and end in ISO
    const end = new Date();
    const start = new Date(Date.now() - 14 * 24 * 3600 * 1000);
    try {
      const history = await this._hass.callWS({
        type: 'history/period',
        start: start.toISOString(),
        end: end.toISOString(),
        filter_entity_id: [entityId],
      });

      // lo storico è un array di array per ogni entità
      const series = (history && history[0]) || [];
      const points = series.map(s => ({
        t: new Date(s.last_changed),
        v: parseFloat(s.state) || null,
      })).filter(p => p.v !== null);

      const labels = points.map(p => p.t.toISOString().split('T')[0]);
      const data = points.map(p => p.v);

      // carica Chart.js in modo lazy se non presente
      await this._ensureChart();
      if (this._chart) {
        this._chart.data.labels = labels;
        this._chart.data.datasets[0].data = data;
        this._chart.update();
      } else {
        this._chart = new Chart(this._canvas.getContext('2d'), {
          type: 'line',
          data: {
            labels: labels,
            datasets: [{
              label: 'Prezzo',
              data: data,
              borderColor: '#3f51b5',
              backgroundColor: 'rgba(63,81,181,0.1)',
              fill: true,
              tension: 0.2,
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
              x: { display: false },
              y: { beginAtZero: false }
            },
            plugins: { legend: { display: false } }
          }
        });
      }
    } catch (err) {
      // ignora errori sullo storico, pulisci il grafico e logga in console
      console.error('Errore recupero storico per', entityId, err);
    }
  }

  _ensureChart() {
    return new Promise((resolve, reject) => {
      if (window.Chart) return resolve();
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/chart.js';
      script.onload = () => resolve();
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  getCardSize() {
    return 3;
  }
}

customElements.define('osservaprezzi-card', OsservaprezziCard);

// Register with Home Assistant Lovelace
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'osservaprezzi-card',
  name: 'Osservaprezzi Card',
  preview: true,
  description: 'Card demo per mostrare logo, carburante, prezzo e grafico 14 giorni'
});
