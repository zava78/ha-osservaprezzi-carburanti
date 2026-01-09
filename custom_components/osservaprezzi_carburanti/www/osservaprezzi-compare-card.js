class OsservaprezziCompareCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this._initialized) return;
    this._update();
  }

  connectedCallback() {
    if (this._initialized) return;
    this._shadow = this.attachShadow({ mode: 'open' });
    const style = document.createElement('style');
    style.textContent = `
      .os-compare { font-family: sans-serif; border:1px solid var(--card-border-color,#ddd); border-radius:8px; padding:12px; background:var(--card-background,#fff)}
      .os-title { font-weight:600; margin-bottom:8px }
      table { width:100%; border-collapse:collapse; margin-bottom:8px }
      td,th { padding:6px 8px; border-bottom:1px solid rgba(0,0,0,0.06); text-align:left }
      .logo { width:28px; height:28px; object-fit:contain }
      canvas { width:100%; height:180px }
      .best-price { background: rgba(76,175,80,0.08); font-weight:700 }
    `;
    this._shadow.appendChild(style);

    this._container = document.createElement('div');
    this._container.className = 'os-compare';
    this._shadow.appendChild(this._container);

    this._title = document.createElement('div');
    this._title.className = 'os-title';
    this._container.appendChild(this._title);

    this._table = document.createElement('table');
    this._container.appendChild(this._table);

    this._canvas = document.createElement('canvas');
    this._container.appendChild(this._canvas);

    this._initialized = true;
  }

  setConfig(config) {
    if (!config || !config.entities || !Array.isArray(config.entities) || config.entities.length < 2) {
      throw new Error('Define at least two entities in `entities` array to compare');
    }
    this._config = config;
  }

  _update() {
    const entities = this._config.entities || [];
    const fuel = this._config.fuel || '';
    this._title.textContent = this._config.title || `Confronto: ${fuel}`;

    // build table header
    this._table.innerHTML = '';
    const thead = document.createElement('thead');
    thead.innerHTML = '<tr><th>Logo</th><th>Distributore</th><th>Prezzo</th></tr>';
    this._table.appendChild(thead);
    const tbody = document.createElement('tbody');
    this._table.appendChild(tbody);

    // populate rows and prepare history fetches
    this._datasets = [];
    const colors = ['#3f51b5','#e91e63','#009688','#ff9800','#607d8b'];
    const rowsData = [];
    entities.forEach((eid, i) => {
      const st = this._hass.states[eid] || {};
      const name = (st.attributes && st.attributes.name) || eid;
      const priceStr = (st && st.state && st.state !== 'unknown') ? st.state : null;
      const priceNum = priceStr ? parseFloat(priceStr) : null;

      const row = document.createElement('tr');
      const logoTd = document.createElement('td');
      const img = document.createElement('img');
      img.className = 'logo';
      img.src = (st.attributes && st.attributes.brand_logo) || (this._config.logos && this._config.logos[i]) || '';
      if (!img.src) img.style.display = 'none';
      logoTd.appendChild(img);
      row.appendChild(logoTd);

      const nameTd = document.createElement('td');
      nameTd.textContent = name;
      row.appendChild(nameTd);

      const priceTd = document.createElement('td');
      priceTd.textContent = priceNum !== null ? `${priceNum} €/l` : 'n/a';
      row.appendChild(priceTd);

      rowsData.push({ eid, idx: i, name, priceNum, rowEl: row });

      // prepare empty dataset for chart (keeps dataset order aligned to entities)
      this._datasets.push({label: name, data: [], borderColor: colors[i % colors.length], backgroundColor: 'rgba(0,0,0,0)', fill:false, tension:0.2});
    });

    // sort rows by numeric price (null treated as Infinity) and append to tbody
    rowsData.sort((a,b)=>{
      const va = a.priceNum===null?Number.POSITIVE_INFINITY:a.priceNum;
      const vb = b.priceNum===null?Number.POSITIVE_INFINITY:b.priceNum;
      return va - vb;
    });
    tbody.innerHTML = '';
    let bestPrice = null;
    for (const r of rowsData) {
      tbody.appendChild(r.rowEl);
      if (r.priceNum !== null && (bestPrice === null || r.priceNum < bestPrice)) bestPrice = r.priceNum;
    }
    // highlight the best price row
    if (bestPrice !== null) {
      rowsData.forEach(r=>{
        if (r.priceNum === bestPrice) r.rowEl.classList.add('best-price');
      });
    }

    // draw combined chart (multi-line)
    this._drawHistories(entities);
  }

  async _drawHistories(entities) {
    const end = new Date();
    const start = new Date(Date.now() - 14 * 24 * 3600 * 1000);
    try {
      // request history for all entities in one call
      const history = await this._hass.callWS({
        type: 'history/period',
        start: start.toISOString(),
        end: end.toISOString(),
        filter_entity_id: entities,
      });

      // normalize labels (dates)
      const labelsSet = new Set();
      const perEntityPoints = entities.map((eid, idx) => {
        const series = (history && history[idx]) || [];
        const pts = series.map(s => ({t: new Date(s.last_changed).toISOString().split('T')[0], v: parseFloat(s.state) || null})).filter(p=>p.v!==null);
        pts.forEach(p=>labelsSet.add(p.t));
        return pts;
      });

      const labels = Array.from(labelsSet).sort();

      // build datasets aligned to labels
      this._datasets.forEach((ds, i) => {
        const pts = perEntityPoints[i] || [];
        const map = new Map(pts.map(p=>[p.t,p.v]));
        ds.data = labels.map(l => map.has(l) ? map.get(l) : null);
      });

      await this._ensureChart();
      if (this._chart) {
        this._chart.data.labels = labels;
        this._chart.data.datasets = this._datasets;
        this._chart.update();
      } else {
        this._chart = new Chart(this._canvas.getContext('2d'), {
          type: 'line',
          data: { labels: labels, datasets: this._datasets },
          options: { responsive:true, maintainAspectRatio:false, plugins:{legend:{display:true}}, scales:{x:{display:false}} }
        });
      }
    } catch (err) {
      console.error('Error fetching histories', err);
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
window.customCards.push({ type:'osservaprezzi-compare-card', name:'Osservaprezzi Compare Card', preview:true, description:'Compare same fuel across multiple stations with chart' });
