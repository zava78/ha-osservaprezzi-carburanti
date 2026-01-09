class OsservaprezziCompareCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) return;
    this._update();
  }

  connectedCallback() {
    if (this._initialized) return;
    this._shadow = this.attachShadow({ mode: 'open' });
    this._container = document.createElement('ha-card');
    this._container.className = 'os-compare';
    const style = document.createElement('style');
    style.textContent = `
      :host { display: block; }
      ha-card {
        padding: 16px;
        display: flex;
        flex-direction: column;
        gap: 16px;
      }
      .header {
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      .title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--primary-text-color);
      }
      .controls {
        display: flex;
        gap: 8px;
      }
      .icon-btn {
        background: none;
        border: 1px solid var(--divider-color, #eee);
        border-radius: 4px;
        cursor: pointer;
        padding: 4px 8px;
        color: var(--secondary-text-color);
        font-size: 0.85rem;
        transition: all 0.2s;
      }
      .icon-btn:hover {
         background: var(--secondary-background-color, #f5f5f5);
      }
      
      .table-responsive {
        width: 100%;
        overflow-x: auto;
      }
      table {
        width: 100%;
        border-collapse: separate; 
        border-spacing: 0;
      }
      th {
        text-align: left;
        color: var(--secondary-text-color);
        font-weight: 500;
        font-size: 0.85rem;
        padding: 8px;
        border-bottom: 2px solid var(--divider-color, #eee);
      }
      td {
        padding: 12px 8px;
        border-bottom: 1px solid var(--divider-color, #f0f0f0);
        vertical-align: middle;
      }
      tr:last-child td { border-bottom: none; }
      
      .st-logo {
        width: 32px; height: 32px;
        object-fit: contain;
        background: #fff;
        border-radius: 50%;
        padding: 2px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
      }
      .st-name {
        font-weight: 500;
        font-size: 0.95rem;
      }
      .st-price {
        font-weight: 700;
        font-size: 1.0rem;
        font-variant-numeric: tabular-nums;
      }
      .best-price .st-price {
        color: var(--success-color, #4caf50);
      }
      .chart-wrap {
        height: 200px;
        width: 100%;
        margin-top: 8px;
      }
    `;
    this._shadow.appendChild(style);
    this._shadow.appendChild(this._container);

    // Header structure
    const header = document.createElement('div');
    header.className = 'header';
    this._titleEl = document.createElement('div');
    this._titleEl.className = 'title';
    header.appendChild(this._titleEl);

    const controls = document.createElement('div');
    controls.className = 'controls';

    this._btnSort = document.createElement('button');
    this._btnSort.className = 'icon-btn';
    this._btnSort.innerText = 'Prezzo ↕';
    this._btnSort.onclick = () => {
      this._sortKey = this._sortKey === 'price' ? 'name' : 'price';
      this._btnSort.innerText = this._sortKey === 'price' ? 'Prezzo ↕' : 'Nome ↕';
      this._update();
    };
    controls.appendChild(this._btnSort);

    header.appendChild(controls);
    this._container.appendChild(header);

    // Table
    const tableWrap = document.createElement('div');
    tableWrap.className = 'table-responsive';
    this._table = document.createElement('table');
    tableWrap.appendChild(this._table);
    this._container.appendChild(tableWrap);

    // Chart
    const chartWrap = document.createElement('div');
    chartWrap.className = 'chart-wrap';
    this._canvas = document.createElement('canvas');
    chartWrap.appendChild(this._canvas);
    this._container.appendChild(chartWrap);

    this._sortKey = 'price';
    this._initialized = true;
  }

  setConfig(config) {
    if (!config || !config.entities || !Array.isArray(config.entities)) {
      throw new Error('Please define entities list');
    }
    this._config = config;
  }

  _update() {
    const entities = this._config.entities;
    const fuel = this._config.fuel || '';
    this._titleEl.innerText = this._config.title || `Confronto ${fuel}`;

    // Header
    this._table.innerHTML = `<thead><tr><th style="width:50px"></th><th>Stazione</th><th style="text-align:right">Prezzo</th></tr></thead>`;
    const tbody = document.createElement('tbody');
    this._table.appendChild(tbody);

    let rows = [];
    entities.forEach((eid, idx) => {
      const state = this._hass.states[eid];
      if (!state) return;
      const price = parseFloat(state.state);
      const name = state.attributes.name || eid;
      const logo = state.attributes.brand_logo || '';

      rows.push({
        eid, idx, price: isNaN(price) ? Infinity : price, name, logo, stateStr: state.state
      });
    });

    // Sort
    rows.sort((a, b) => {
      if (this._sortKey === 'price') return a.price - b.price;
      return a.name.localeCompare(b.name);
    });

    // Find best
    const bestPrice = Math.min(...rows.map(r => r.price));

    rows.forEach(r => {
      const tr = document.createElement('tr');
      if (Math.abs(r.price - bestPrice) < 0.001 && r.price !== Infinity) tr.classList.add('best-price');

      tr.innerHTML = `
            <td><img src="${r.logo}" class="st-logo" onerror="this.style.display='none'"></td>
            <td class="st-name">${r.name.replace('Distributore', '').replace('Stazione', '')}</td>
            <td style="text-align:right" class="st-price">${r.price !== Infinity ? r.stateStr + ' €' : '--'}</td>
        `;
      tbody.appendChild(tr);
    });

    this._drawHistories(entities);
  }

  async _drawHistories(entities) {
    const end = new Date();
    const start = new Date(Date.now() - 14 * 24 * 3600 * 1000);
    try {
      const history = await this._hass.callWS({
        type: 'history/period',
        start: start.toISOString(),
        end: end.toISOString(),
        filter_entity_id: entities,
      });

      const datasets = [];
      // Colors from Material Design
      const colors = ['#2196f3', '#f44336', '#4caf50', '#ff9800', '#9c27b0', '#00bcd4', '#795548'];

      entities.forEach((eid, i) => {
        const series = history[i] || [];
        const pts = series.map(s => ({ x: new Date(s.last_changed).toISOString().split('T')[0], y: parseFloat(s.state) })).filter(p => !isNaN(p.y));

        // Basic aggregation (last price per day for simplicity in chart)
        const distinctDays = {};
        pts.forEach(p => distinctDays[p.x] = p.y);

        datasets.push({
          label: this._hass.states[eid]?.attributes?.name || eid,
          data: Object.keys(distinctDays).sort().map(d => ({ x: d, y: distinctDays[d] })),
          borderColor: colors[i % colors.length],
          backgroundColor: 'transparent',
          tension: 0.3,
          pointRadius: 2
        });
      });

      await this._ensureChart();
      if (this._chart) {
        this._chart.data.datasets = datasets;
        this._chart.update();
      } else {
        this._chart = new Chart(this._canvas.getContext('2d'), {
          type: 'line',
          data: { datasets },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            scales: { x: { type: 'category' } },
            plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } }
          }
        });
      }

    } catch (e) {
      console.error(e);
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

  getCardSize() { return 4; }
}

customElements.define('osservaprezzi-compare-card', OsservaprezziCompareCard);

window.customCards = window.customCards || [];
window.customCards.push({ type: 'osservaprezzi-compare-card', name: 'Osservaprezzi Compare Card', preview: true, description: 'Confronta lo stesso carburante su più stazioni con grafico' });
