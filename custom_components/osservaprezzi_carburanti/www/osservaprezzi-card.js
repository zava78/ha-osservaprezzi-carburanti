class OsservaprezziCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) return;
    this._update();
  }

  connectedCallback() {
    if (this._initialized) return;
    this._shadow = this.attachShadow({ mode: 'open' });
    this._container = document.createElement('ha-card');
    this._container.className = 'os-card';
    const style = document.createElement('style');
    style.textContent = `
      :host { display: block; }
      ha-card {
        cursor: pointer;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        height: 100%;
        box-sizing: border-box;
      }
      .os-content { padding: 16px; flex: 1; }
      .os-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
      .os-logo-wrap {
        width: 40px; height: 40px;
        background: #fff;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        padding: 4px;
      }
      .os-logo { width: 100%; height: 100%; object-fit: contain; }
      .os-meta { text-align: right; }
      .os-fuel {
        font-size: 0.85rem;
        text-transform: uppercase;
        color: var(--secondary-text-color);
        letter-spacing: 0.5px;
        font-weight: 500;
        opacity: 0.8;
      }
      .os-station {
        font-size: 1.1rem;
        font-weight: 600;
        margin-top: 2px;
        color: var(--primary-text-color);
        line-height: 1.2;
      }
      .os-price-wrap {
        margin-top: 16px;
        display: flex;
        align-items: baseline;
        gap: 4px;
      }
      .os-price {
        font-size: 2.2rem;
        font-weight: 700;
        color: var(--primary-color, #03a9f4);
        line-height: 1;
      }
      .os-unit {
        font-size: 1.0rem;
        color: var(--secondary-text-color);
        font-weight: 500;
      }
      .os-chart-container {
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 80px;
        opacity: 0.6;
        pointer-events: none;
      }
      canvas { width: 100%; height: 100%; }
    `;
    this._shadow.appendChild(style);
    this._shadow.appendChild(this._container);

    // Content Wrapper
    const content = document.createElement('div');
    content.className = 'os-content';
    this._container.appendChild(content);

    // Header
    const header = document.createElement('div');
    header.className = 'os-header';

    // Logo
    this._logoWrap = document.createElement('div');
    this._logoWrap.className = 'os-logo-wrap';
    this._logo = document.createElement('img');
    this._logo.className = 'os-logo';
    this._logoWrap.appendChild(this._logo);
    header.appendChild(this._logoWrap);

    // Meta (Start on the right for clean look)
    const meta = document.createElement('div');
    meta.className = 'os-meta';
    this._fuel = document.createElement('div');
    this._fuel.className = 'os-fuel';
    this._station = document.createElement('div');
    this._station.className = 'os-station';
    meta.appendChild(this._fuel);
    meta.appendChild(this._station);
    header.appendChild(meta);
    content.appendChild(header);

    // Price
    const priceWrap = document.createElement('div');
    priceWrap.className = 'os-price-wrap';
    this._price = document.createElement('div');
    this._price.className = 'os-price';
    const unit = document.createElement('div');
    unit.className = 'os-unit';
    unit.textContent = '€/l';
    priceWrap.appendChild(this._price);
    priceWrap.appendChild(unit);
    content.appendChild(priceWrap);

    // Chart
    this._chartContainer = document.createElement('div');
    this._chartContainer.className = 'os-chart-container';
    this._canvas = document.createElement('canvas');
    this._chartContainer.appendChild(this._canvas);
    this._container.appendChild(this._chartContainer);

    this._initialized = true;
  }

  setConfig(config) {
    if (!config || !config.entity) {
      throw new Error('Please define an entity');
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

    if (logo) {
      this._logo.src = logo;
      this._logoWrap.style.display = 'flex';
    } else {
      this._logoWrap.style.display = 'none';
    }

    // truncate name if too long
    const cleanName = name.replace('Distributore ', '').replace('Stazione ', '');
    this._station.textContent = cleanName.length > 25 ? cleanName.substring(0, 25) + '...' : cleanName;

    this._fuel.textContent = fuel;
    this._price.textContent = price && price !== 'unknown' ? price : '--.--';

    this._drawHistory(entityId);
  }

  async _drawHistory(entityId) {
    const end = new Date();
    const start = new Date(Date.now() - 14 * 24 * 3600 * 1000);
    try {
      const history = await this._hass.callWS({
        type: 'history/period',
        start: start.toISOString(),
        end: end.toISOString(),
        filter_entity_id: [entityId],
      });

      const series = (history && history[0]) || [];
      const points = series.map(s => ({
        t: new Date(s.last_changed),
        v: parseFloat(s.state) || null,
      })).filter(p => p.v !== null);

      const labels = points.map(p => p.t.toISOString().split('T')[0]);
      const data = points.map(p => p.v);

      await this._ensureChart();
      if (this._chart) {
        this._chart.data.labels = labels;
        this._chart.data.datasets[0].data = data;
        this._chart.update();
      } else {
        const ctx = this._canvas.getContext('2d');
        const gradient = ctx.createLinearGradient(0, 0, 0, 80);
        // Get card primary color or fallback
        const color = getComputedStyle(this._container).getPropertyValue('--primary-color').trim() || '#2196f3';
        gradient.addColorStop(0, color);
        gradient.addColorStop(1, 'rgba(255, 255, 255, 0)');

        this._chart = new Chart(this._canvas.getContext('2d'), {
          type: 'line',
          data: {
            labels: labels,
            datasets: [{
              data: data,
              borderColor: color,
              borderWidth: 2,
              backgroundColor: gradient,
              fill: true,
              pointRadius: 0,
              tension: 0.4,
            }]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            layout: { padding: 0 },
            scales: {
              x: { display: false },
              y: { display: false }
            },
            plugins: { legend: { display: false }, tooltip: { enabled: false } }
          }
        });
      }
    } catch (err) {
      console.error('Error fetching history', err);
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
    return 2;
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
