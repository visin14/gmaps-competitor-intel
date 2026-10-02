const ScrapingPage = {
  activeJobId: null,
  pollTimer: null,
  _competitors: [],
  
  async render(container) {
    if (!AppState.currentProject) {
      container.innerHTML = renderNoProject('Scraping');
      return;
    }
    
    // Fetch competitors for this project
    const res = await API.getCompetitors(AppState.currentProject.id).catch(() => ({data:[]}));
    this._competitors = res.data || [];
    
    container.innerHTML = `
      <div class="scraping-page">
        <div class="page-header">
          <h2>🔍 Scraping</h2>
          <p class="text-secondary">Collect Google Maps updates from competitor profiles</p>
        </div>
        
        <!-- Start New Scrape Section -->
        <div class="card" id="start-scrape-section">
          <h3>Start New Scrape Job</h3>
          <div class="form-group">
            <div class="select-all-row">
              <label><input type="checkbox" id="select-all-competitors" onchange="ScrapingPage.toggleSelectAll(this.checked)"> Select All</label>
              <span class="text-secondary">${this._competitors.length} competitors</span>
            </div>
          </div>
          <div class="competitor-checklist" id="competitor-checklist">
            ${this._competitors.length === 0 ? '<p class="text-secondary">No competitors added yet. <a href="#" onclick="navigateTo(\'competitors\')">Add competitors</a> first.</p>' :
              this._competitors.map(c => `
                <label class="competitor-check-item">
                  <input type="checkbox" class="comp-checkbox" value="${c.id}" checked>
                  <div class="comp-check-info">
                    <span class="comp-check-name">${escapeHtml(c.name)}</span>
                    <span class="badge badge-${c.scrape_status}">${c.scrape_status}</span>
                    <span class="text-secondary text-sm">${c.total_posts} posts</span>
                  </div>
                </label>
              `).join('')
            }
          </div>
          <div class="mt-16">
            <button class="btn btn-primary" id="start-scrape-btn" onclick="ScrapingPage.startScrape()" ${this._competitors.length === 0 ? 'disabled' : ''}>
              🔍 Start Scraping
            </button>
          </div>
        </div>
        
        <!-- Active Job Panel (hidden by default) -->
        <div class="card hidden" id="active-job-panel">
          <h3>⚡ Active Scrape Job</h3>
          
          <!-- CAPTCHA Alert -->
          <div class="captcha-alert hidden" id="captcha-alert">
            <div class="captcha-alert-icon">⚠️</div>
            <div class="captcha-alert-content">
              <h4>Manual Verification Required</h4>
              <p>Google has shown a CAPTCHA or verification screen. Please open the browser window that launched, complete the verification, then click Resume.</p>
              <button class="btn btn-warning" onclick="ScrapingPage.resumeJob()">▶ Resume Scraping</button>
            </div>
          </div>
          
          <div class="progress-section">
            <div class="progress-labels">
              <span id="progress-text">Processing...</span>
              <span id="progress-percent">0%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" id="progress-fill" style="width:0%"></div>
            </div>
          </div>
          
          <div class="log-section">
            <h4>Live Log</h4>
            <table class="log-table">
              <thead><tr><th>Competitor</th><th>Status</th><th>New Posts</th><th>Duplicates</th><th>Details</th></tr></thead>
              <tbody id="live-log-body"></tbody>
            </table>
          </div>
        </div>
        
        <!-- History Section -->
        <div class="card" id="scrape-history-section">
          <h3>📋 Scrape History</h3>
          <div id="history-content">Loading...</div>
        </div>

        <!-- Detailed per-competitor logs -->
        <div class="card" id="scrape-logs-section">
          <h3>🧾 Detailed Scrape Logs</h3>
          <div id="logs-content">Loading...</div>
        </div>
      </div>
    `;
    
    this.loadHistory();
    this.loadLogs();

    // If there's already an active job, resume polling
    if (this.activeJobId) {
      this.startPolling(this.activeJobId);
    }
  },
  
  toggleSelectAll(checked) {
    document.querySelectorAll('.comp-checkbox').forEach(cb => cb.checked = checked);
  },
  
  async startScrape() {
    const selected = [...document.querySelectorAll('.comp-checkbox:checked')].map(cb => parseInt(cb.value));
    if (selected.length === 0) { Toast.warning('Select at least one competitor'); return; }
    
    try {
      const res = await API.startScrape(AppState.currentProject.id, selected);
      const jobId = res.data.job_id;
      this.activeJobId = jobId;
      document.getElementById('active-job-panel').classList.remove('hidden');
      Toast.info('Scrape job started!');
      this.startPolling(jobId);
    } catch (err) {
      Toast.error(err.message);
    }
  },
  
  startPolling(jobId) {
    if (this.pollTimer) clearInterval(this.pollTimer);
    this.pollTimer = setInterval(() => this.pollJobStatus(jobId), 3000);
    this.pollJobStatus(jobId);
  },
  
  async pollJobStatus(jobId) {
    try {
      const res = await API.getJobStatus(jobId);
      const job = res.data;
      
      // Update progress
      const pct = job.total_competitors > 0 ? Math.round((job.processed_competitors / job.total_competitors) * 100) : 0;
      const fill = document.getElementById('progress-fill');
      const ptext = document.getElementById('progress-text');
      const ppct = document.getElementById('progress-percent');
      if (fill) fill.style.width = pct + '%';
      if (ptext) ptext.textContent = `Processing ${job.processed_competitors} of ${job.total_competitors} competitors...`;
      if (ppct) ppct.textContent = pct + '%';
      
      // Show CAPTCHA alert
      const captchaAlert = document.getElementById('captcha-alert');
      if (captchaAlert) {
        captchaAlert.classList.toggle('hidden', job.status !== 'awaiting_verification');
      }
      
      // Update log table
      const tbody = document.getElementById('live-log-body');
      if (tbody && job.logs) {
        tbody.innerHTML = job.logs.map(log => `
          <tr>
            <td>${escapeHtml(log.competitor_name || '-')}</td>
            <td><span class="badge badge-${log.status || 'idle'}">${log.status || 'pending'}</span></td>
            <td>${log.new_posts || 0}</td>
            <td>${log.duplicates_skipped || 0}</td>
            <td class="text-secondary text-sm">${escapeHtml(log.error_info || '-')}</td>
          </tr>
        `).join('');
      }
      
      // Stop polling if done
      if (['done', 'failed', 'partial'].includes(job.status)) {
        this.stopPolling();
        const msg = `Scrape job ${job.status === 'partial' ? 'finished with some failures' : job.status}`;
        job.status === 'done' ? Toast.success(msg) : Toast.warning(msg);
        this.loadHistory();
        this.loadLogs();
      }
    } catch (err) {
      console.error('Poll error:', err);
    }
  },
  
  stopPolling() {
    if (this.pollTimer) { clearInterval(this.pollTimer); this.pollTimer = null; }
  },
  
  async resumeJob() {
    if (!this.activeJobId) return;
    try {
      await API.resumeJob(this.activeJobId);
      Toast.info('Resuming scrape...');
      document.getElementById('captcha-alert')?.classList.add('hidden');
    } catch (err) {
      Toast.error(err.message);
    }
  },
  
  async loadLogs() {
    const el = document.getElementById('logs-content');
    if (!el || !AppState.currentProject) return;
    try {
      const res = await API.getScrapeLogs(AppState.currentProject.id);
      const logs = res.data || [];
      if (logs.length === 0) { el.innerHTML = '<p class="text-secondary">No scrape logs yet.</p>'; return; }
      el.innerHTML = `
        <div class="full-log-wrapper">
          <table class="log-table">
            <thead><tr><th>Job</th><th>Competitor</th><th>Start</th><th>End</th><th>Found</th><th>New</th><th>Dupes</th><th>Images</th><th>Status</th><th>Manual verification</th><th>Error</th></tr></thead>
            <tbody>
              ${logs.slice(0, 100).map(l => `
                <tr>
                  <td>#${l.job_id}</td>
                  <td>${escapeHtml(l.competitor_name || '-')}</td>
                  <td>${formatDate(l.start_time)}</td>
                  <td>${l.end_time ? formatDate(l.end_time) : '-'}</td>
                  <td>${l.posts_found}</td><td>${l.new_posts}</td><td>${l.duplicates_skipped}</td><td>${l.images_downloaded}</td>
                  <td><span class="badge badge-${l.status || 'idle'}">${l.status || '-'}</span></td>
                  <td>${l.manual_intervention ? '⚠️ required' : (l.captcha_encountered ? 'captcha' : '-')}</td>
                  <td class="text-secondary text-sm">${escapeHtml(l.error_info || '-')}</td>
                </tr>`).join('')}
            </tbody>
          </table>
        </div>`;
    } catch (err) {
      el.innerHTML = '<p class="text-secondary">Failed to load logs.</p>';
    }
  },

  async loadHistory() {
    const el = document.getElementById('history-content');
    if (!el || !AppState.currentProject) return;
    try {
      const res = await API.getScrapeJobs(AppState.currentProject.id);
      const jobs = res.data || [];
      if (jobs.length === 0) {
        el.innerHTML = '<p class="text-secondary">No scrape jobs yet.</p>';
        return;
      }
      el.innerHTML = `
        <table class="log-table">
          <thead><tr><th>Job ID</th><th>Started</th><th>Status</th><th>Competitors</th><th>New Posts</th><th>Duplicates</th></tr></thead>
          <tbody>
            ${jobs.map(j => `
              <tr>
                <td>#${j.id}</td>
                <td>${formatDate(j.started_at)}</td>
                <td><span class="badge badge-${j.status}">${j.status}</span></td>
                <td>${j.processed_competitors}/${j.total_competitors}</td>
                <td>${j.summary?.new_posts || 0}</td>
                <td>${j.summary?.duplicates_skipped || 0}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    } catch (err) {
      el.innerHTML = '<p class="text-secondary">Failed to load history.</p>';
    }
  }
};
