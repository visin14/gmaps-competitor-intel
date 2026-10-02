const AnalysisPage = {
  pollTimer: null,
  
  async render(container) {
    if (!AppState.currentProject) {
      container.innerHTML = renderNoProject('AI Analysis');
      return;
    }
    
    container.innerHTML = `
      <div class="analysis-page">
        <div class="page-header">
          <h2>🧠 AI Analysis</h2>
          <p class="text-secondary">Analyze competitor posts with AI to extract topics, keywords and patterns</p>
        </div>
        
        <div class="card" id="analysis-status-card">
          <div class="analysis-status-header">
            <div>
              <h3>Analysis Status</h3>
              <p class="text-secondary" id="analysis-status-text">Loading...</p>
            </div>
            <button class="btn btn-primary" id="run-analysis-btn" onclick="AnalysisPage.runAnalysis()">▶ Run AI Analysis</button>
          </div>
          <div class="progress-bar mt-16">
            <div class="progress-fill" id="analysis-progress-fill" style="width:0%"></div>
          </div>
          <div class="analysis-meta mt-8">
            <span id="analysis-count-text" class="text-secondary"></span>
            <span class="ai-provider-badge">🤖 Gemini + Grok</span>
          </div>
        </div>
        
        <div class="card" id="analysis-results-card">
          <div class="card-header-row">
            <h3>Analysis Results</h3>
            <select class="form-select select-sm" id="filter-content-type" onchange="AnalysisPage.loadResults()">
              <option value="">All Content Types</option>
              <option>Promotional</option>
              <option>Educational</option>
              <option>Engagement</option>
              <option>Seasonal</option>
              <option>Announcement</option>
            </select>
          </div>
          <div id="analysis-results">Loading results...</div>
        </div>
      </div>
    `;
    
    this.loadStatus();
    this.loadResults();
  },
  
  async loadStatus() {
    try {
      const res = await API.getAnalysisStatus(AppState.currentProject.id);
      const s = res.data;
      const pct = s.total_posts > 0 ? Math.round((s.analyzed_posts / s.total_posts) * 100) : 0;
      document.getElementById('analysis-status-text').textContent = `${s.analyzed_posts} of ${s.total_posts} posts analyzed`;
      document.getElementById('analysis-progress-fill').style.width = pct + '%';
      document.getElementById('analysis-count-text').textContent = `${s.pending_posts} posts pending analysis`;
    } catch {}
  },
  
  async runAnalysis() {
    const btn = document.getElementById('run-analysis-btn');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Analyzing...'; }
    try {
      await API.runAnalysis(AppState.currentProject.id);
      Toast.info('Analysis started in background. This may take a moment.');
      // Poll status
      if (this.pollTimer) clearInterval(this.pollTimer);
      this.pollTimer = setInterval(async () => {
        await this.loadStatus();
        const res = await API.getAnalysisStatus(AppState.currentProject.id);
        if (res.data.pending_posts === 0) {
          clearInterval(this.pollTimer);
          this.pollTimer = null;
          Toast.success('Analysis complete!');
          if (btn) { btn.disabled = false; btn.textContent = '▶ Run AI Analysis'; }
          this.loadResults();
        }
      }, 3000);
    } catch (err) {
      Toast.error(err.message);
      if (btn) { btn.disabled = false; btn.textContent = '▶ Run AI Analysis'; }
    }
  },
  
  async loadResults() {
    const el = document.getElementById('analysis-results');
    if (!el) return;
    try {
      const res = await API.getAnalysisResults(AppState.currentProject.id);
      const posts = res.data?.posts || [];
      const filterType = document.getElementById('filter-content-type')?.value;
      const filtered = filterType ? posts.filter(p => p.ai_content_type === filterType) : posts;
      
      if (filtered.length === 0) {
        el.innerHTML = '<p class="text-secondary">No analyzed posts yet. Click "Run AI Analysis" to start.</p>';
        return;
      }
      
      el.innerHTML = `
        <div class="analysis-table-wrapper">
          <table class="log-table">
            <thead>
              <tr>
                <th>Competitor</th>
                <th>Main Topic</th>
                <th>Sub-Topic</th>
                <th>Content Type</th>
                <th>Keywords</th>
                <th>CTA</th>
                <th>Offer</th>
              </tr>
            </thead>
            <tbody>
              ${filtered.map(p => `
                <tr>
                  <td>${escapeHtml(p.competitor_name || '-')}</td>
                  <td>${escapeHtml(p.ai_main_topic || '-')}</td>
                  <td class="text-secondary">${escapeHtml(p.ai_sub_topic || '-')}</td>
                  <td><span class="badge content-type-${(p.ai_content_type||'').toLowerCase()}">${escapeHtml(p.ai_content_type || '-')}</span></td>
                  <td>${(Array.isArray(p.ai_keywords) ? p.ai_keywords : []).slice(0,3).map(k => `<span class="keyword-chip">${escapeHtml(k)}</span>`).join('')}</td>
                  <td class="text-secondary">${escapeHtml(p.ai_cta || '-')}</td>
                  <td class="text-secondary">${escapeHtml(p.ai_offer_pattern || '-')}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
    } catch (err) {
      el.innerHTML = `<p class="text-secondary">Failed to load: ${escapeHtml(err.message)}</p>`;
    }
  }
};
