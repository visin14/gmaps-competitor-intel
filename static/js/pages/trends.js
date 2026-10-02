const TrendsPage = {
  async render(container) {
    if (!AppState.currentProject) {
      container.innerHTML = renderNoProject('Trends');
      return;
    }
    
    container.innerHTML = `
      <div class="trends-page">
        <div class="page-header">
          <h2>📈 Trend Analysis</h2>
          <p class="text-secondary">Discover what topics dominate competitor content</p>
        </div>
        
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;">
            <h3>Topic Trends</h3>
            <button class="btn btn-primary" onclick="TrendsPage.calculateTrends()">🔄 Calculate Trends</button>
          </div>
          <div id="trends-content"><div class="loading-page"><div class="loading-spinner"></div></div></div>
        </div>
        
        <div class="card">
          <h3>Top Keywords</h3>
          <div id="keywords-content"><div class="loading-page"><div class="loading-spinner"></div></div></div>
        </div>

        <div class="card">
          <h3>Competitor Publishing Patterns</h3>
          <div id="patterns-content"><div class="loading-page"><div class="loading-spinner"></div></div></div>
        </div>
      </div>
    `;

    this.loadTrends();
    this.loadKeywords();
    this.loadPatterns();
  },

  async loadPatterns() {
    const el = document.getElementById('patterns-content');
    if (!el) return;
    try {
      const rows = (await API.getPatterns(AppState.currentProject.id)).data || [];
      if (rows.length === 0) { el.innerHTML = '<p class="text-secondary">No competitors yet.</p>'; return; }
      el.innerHTML = `
        <div class="full-log-wrapper"><table class="log-table pattern-table">
          <thead><tr><th>Competitor</th><th>Posts</th><th>Posts / week</th><th>Top topics</th><th>Top CTA</th><th>Posts with offers</th><th>Last post</th></tr></thead>
          <tbody>${rows.map(r => `
            <tr>
              <td>${escapeHtml(r.competitor_name)}</td><td>${r.total_posts}</td>
              <td>${r.posts_per_week ?? '-'}</td>
              <td>${r.top_topics.map(t => `<span class="topic-chip">${escapeHtml(t.topic)} (${t.count})</span>`).join(' ') || '-'}</td>
              <td>${escapeHtml(r.top_cta || '-')}</td><td>${r.offer_share}%</td><td>${r.last_post_date || '-'}</td>
            </tr>`).join('')}</tbody>
        </table></div>`;
    } catch (err) {
      el.innerHTML = `<p class="text-secondary">${escapeHtml(err.message)}</p>`;
    }
  },
  
  async calculateTrends() {
    try {
      await API.calculateTrends(AppState.currentProject.id);
      Toast.success('Trends calculated!');
      this.loadTrends();
    } catch (err) {
      Toast.error(err.message);
    }
  },
  
  async loadTrends() {
    const el = document.getElementById('trends-content');
    if (!el) return;
    try {
      const res = await API.getTrends(AppState.currentProject.id);
      const trends = res.data || [];
      
      if (trends.length === 0) {
        el.innerHTML = '<p class="text-secondary">No trend data yet. Click "Calculate Trends" (AI analysis must be run first).</p>';
        return;
      }
      
      el.innerHTML = `
        <div class="trends-layout">
          <div class="trends-charts">
            <canvas id="trends-donut" height="250"></canvas>
          </div>
          <div class="trends-table-col">
            <table class="log-table">
              <thead><tr><th>Topic</th><th>Posts</th><th>Competitors</th><th>% Coverage</th></tr></thead>
              <tbody>
                ${trends.map(t => `
                  <tr>
                    <td><span class="topic-chip">${escapeHtml(t.topic)}</span></td>
                    <td>${t.occurrence_count}</td>
                    <td>${t.competitor_count}/${t.total_competitors}</td>
                    <td>
                      <div class="trend-bar-row">
                        <div class="trend-bar-bg"><div class="trend-fill" style="width:${Math.min(t.percentage,100)}%"></div></div>
                        <span>${t.percentage ? t.percentage.toFixed(0) : 0}%</span>
                      </div>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
        <canvas id="trends-bar" height="200" class="mt-16"></canvas>
      `;
      
      const labels = trends.map(t => t.topic);
      const data = trends.map(t => t.occurrence_count);
      setTimeout(() => {
        Charts.createDonut('trends-donut', labels, data);
        Charts.createTrendBar('trends-bar', labels, data);
      }, 100);
    } catch (err) {
      el.innerHTML = `<p class="text-secondary">${escapeHtml(err.message)}</p>`;
    }
  },
  
  async loadKeywords() {
    const el = document.getElementById('keywords-content');
    if (!el) return;
    try {
      const res = await API.getTrendKeywords(AppState.currentProject.id);
      const keywords = res.data || [];
      
      if (keywords.length === 0) {
        el.innerHTML = '<p class="text-secondary">No keyword data yet. Run AI analysis first.</p>';
        return;
      }
      
      const maxCount = Math.max(...keywords.map(k => k.count));
      el.innerHTML = `
        <div class="keyword-cloud">
          ${keywords.map(k => {
            const size = Math.max(0.8, (k.count / maxCount) * 1.8);
            return `<span class="keyword-tag" style="font-size:${size}em" title="${k.count} occurrences">${escapeHtml(k.keyword)} <span class="kw-count">${k.count}</span></span>`;
          }).join('')}
        </div>
        <div class="mt-16">
          <canvas id="keywords-chart" height="150"></canvas>
        </div>
      `;
      
      setTimeout(() => {
        Charts.createTrendBar('keywords-chart', keywords.slice(0,10).map(k => k.keyword), keywords.slice(0,10).map(k => k.count));
      }, 100);
    } catch (err) {
      el.innerHTML = `<p class="text-secondary">${escapeHtml(err.message)}</p>`;
    }
  }
};
