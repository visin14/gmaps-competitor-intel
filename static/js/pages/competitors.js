const CompetitorsPage = {
  async render(container) {
    if (!AppState.currentProject) {
      container.innerHTML = renderNoProject('Competitors');
      return;
    }
    
    container.innerHTML = '<div class="loading-page"><div class="loading-spinner"></div></div>';
    
    try {
      const res = await API.getCompetitors(AppState.currentProject.id);
      const competitors = res.data || [];
      
      container.innerHTML = `
        <div class="page-header">
          <div>
            <h2>Competitors</h2>
            <p class="text-secondary">Manage competitors for ${escapeHtml(AppState.currentProject.name)}</p>
          </div>
          <div>
            <button class="btn btn-secondary" onclick="CompetitorsPage.startScrapeAll()" ${competitors.length === 0 ? 'disabled' : ''}>🔍 Scrape All</button>
            <button class="btn btn-primary" onclick="CompetitorsPage.showAddModal()">+ Add Competitor</button>
          </div>
        </div>
        ${competitors.length === 0 ? `
          <div class="empty-state">
            <div class="empty-icon">🏢</div>
            <h3>No Competitors Yet</h3>
            <p>Add your first competitor to start tracking their Google Maps activity.</p>
            <button class="btn btn-primary" onclick="CompetitorsPage.showAddModal()">Add Competitor</button>
          </div>
        ` : `
          <div class="cards-grid">
            ${competitors.map(c => CompetitorsPage.renderCard(c)).join('')}
          </div>
        `}
      `;
    } catch (err) {
      Toast.error(err.message);
    }
  },
  
  renderCard(c) {
    return `
      <div class="card competitor-card">
        <div class="project-card-header">
          <div class="project-card-icon">🏢</div>
          <div>
            <h3>${escapeHtml(c.name)}</h3>
            <a href="${escapeHtml(c.google_maps_url)}" target="_blank" class="link text-sm">${truncate(escapeHtml(c.google_maps_url), 40)}</a>
          </div>
        </div>
        <div class="project-stats">
          <div class="project-stat">
            <span class="stat-num">${c.total_posts || 0}</span>
            <span class="stat-lbl">Posts</span>
          </div>
          <div class="project-stat">
            <span class="badge badge-${c.scrape_status || 'idle'}">${c.scrape_status || 'idle'}</span>
            <span class="text-secondary text-sm mt-8">${c.last_scraped_at ? 'Scraped ' + formatRelativeTime(c.last_scraped_at) : 'Never scraped'}</span>
          </div>
        </div>
        <div class="project-card-footer">
          <button class="btn btn-sm btn-primary" onclick="CompetitorsPage.scrapeOne(${c.id})">Scrape</button>
          <div class="project-actions">
            <button class="btn btn-sm btn-secondary" onclick="CompetitorsPage.showEditModal(${JSON.stringify(c).replace(/"/g, '&quot;')})">Edit</button>
            <button class="btn btn-sm btn-danger" onclick="CompetitorsPage.deleteCompetitor(${c.id})">Delete</button>
          </div>
        </div>
      </div>
    `;
  },
  
  showAddModal() {
    Modal.open('Add Competitor', `
      <form id="competitor-form">
        <div class="form-group">
          <label class="form-label">Competitor Name *</label>
          <input type="text" id="comp-name" class="form-input" required>
        </div>
        <div class="form-group">
          <label class="form-label">Google Maps URL *</label>
          <input type="url" id="comp-url" class="form-input" required placeholder="https://maps.google.com/...">
        </div>
      </form>
    `, `
      <button class="btn btn-secondary" onclick="Modal.close()">Cancel</button>
      <button class="btn btn-primary" onclick="CompetitorsPage.addCompetitor()">Add Competitor</button>
    `);
  },
  
  showEditModal(c) {
    Modal.open('Edit Competitor', `
      <form id="competitor-form">
        <input type="hidden" id="comp-id" value="${c.id}">
        <div class="form-group">
          <label class="form-label">Competitor Name *</label>
          <input type="text" id="comp-name" class="form-input" value="${escapeHtml(c.name)}" required>
        </div>
        <div class="form-group">
          <label class="form-label">Google Maps URL *</label>
          <input type="url" id="comp-url" class="form-input" value="${escapeHtml(c.google_maps_url)}" required>
        </div>
      </form>
    `, `
      <button class="btn btn-secondary" onclick="Modal.close()">Cancel</button>
      <button class="btn btn-primary" onclick="CompetitorsPage.updateCompetitor()">Save Changes</button>
    `);
  },
  
  async addCompetitor() {
    const name = document.getElementById('comp-name')?.value?.trim();
    const url = document.getElementById('comp-url')?.value?.trim();
    if (!name || !url) { Toast.error('Name and URL are required'); return; }
    
    try {
      await API.addCompetitor(AppState.currentProject.id, { name, google_maps_url: url });
      Modal.close();
      Toast.success('Competitor added!');
      this.render(document.getElementById('page-container'));
    } catch (err) {
      Toast.error(err.message);
    }
  },
  
  async updateCompetitor() {
    const id = document.getElementById('comp-id')?.value;
    const name = document.getElementById('comp-name')?.value?.trim();
    const url = document.getElementById('comp-url')?.value?.trim();
    if (!name || !url) { Toast.error('Name and URL are required'); return; }
    
    try {
      await API.updateCompetitor(id, { name, google_maps_url: url });
      Modal.close();
      Toast.success('Competitor updated!');
      this.render(document.getElementById('page-container'));
    } catch (err) {
      Toast.error(err.message);
    }
  },
  
  deleteCompetitor(id) {
    Modal.confirm('Delete Competitor', 'Are you sure you want to delete this competitor and all their scraped posts?', async () => {
      try {
        await API.deleteCompetitor(id);
        Toast.success('Competitor deleted');
        this.render(document.getElementById('page-container'));
      } catch (err) {
        Toast.error(err.message);
      }
    }, 'Delete', true);
  },
  
  async scrapeOne(id) {
    try {
      await API.startScrape(AppState.currentProject.id, [id]);
      navigateTo('scraping');
    } catch (err) {
      Toast.error(err.message);
    }
  },
  
  async startScrapeAll() {
    try {
      const res = await API.getCompetitors(AppState.currentProject.id);
      const competitors = res.data || [];
      if (competitors.length === 0) return;
      const ids = competitors.map(c => c.id);
      await API.startScrape(AppState.currentProject.id, ids);
      navigateTo('scraping');
    } catch (err) {
      Toast.error(err.message);
    }
  }
};
