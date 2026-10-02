const Charts = {
  _instances: {},
  
  _colors: [
    '#7c3aed', '#06b6d4', '#10b981', '#f59e0b', '#ef4444',
    '#8b5cf6', '#0ea5e9', '#14b8a6', '#f97316', '#ec4899'
  ],
  
  _destroy(canvasId) {
    if (this._instances[canvasId]) {
      this._instances[canvasId].destroy();
      delete this._instances[canvasId];
    }
  },
  
  createTrendBar(canvasId, labels, data) {
    this._destroy(canvasId);
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;
    this._instances[canvasId] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [{ data, backgroundColor: this._colors, borderRadius: 6, borderSkipped: false }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
          y: { grid: { display: false }, ticks: { color: '#f1f5f9' } }
        }
      }
    });
  },
  
  createDonut(canvasId, labels, data) {
    this._destroy(canvasId);
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;
    this._instances[canvasId] = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{ data, backgroundColor: this._colors, borderWidth: 0, hoverOffset: 4 }]
      },
      options: {
        responsive: true,
        cutout: '65%',
        plugins: {
          legend: { position: 'right', labels: { color: '#94a3b8', padding: 12, font: { size: 12 } } }
        }
      }
    });
  },
  
  createLine(canvasId, labels, data, label = 'Posts') {
    this._destroy(canvasId);
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;
    this._instances[canvasId] = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{ label, data, borderColor: '#7c3aed', backgroundColor: 'rgba(124,58,237,0.1)', fill: true, tension: 0.4, pointBackgroundColor: '#7c3aed' }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
          y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
        }
      }
    });
  },
  
  destroyAll() {
    Object.keys(this._instances).forEach(id => this._destroy(id));
  }
};
