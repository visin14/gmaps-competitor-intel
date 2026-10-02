const KeywordsPage = {
  async render(container) {
    if (!AppState.currentProject) {
      container.innerHTML = renderNoProject('Keywords');
      return;
    }
    
    container.innerHTML = `
      <div class="page-header">
        <h2>Keywords</h2>
        <p class="text-secondary">Manage discovery keywords for ${escapeHtml(AppState.currentProject.name)}</p>
      </div>
      
      <div class="alert alert-info mb-16">
        ℹ️ Keywords can be used as an additional discovery mechanism to find competitor businesses. Currently, competitors must be added manually.
      </div>
      
      <div class="card">
        <h3>Add Keyword</h3>
        <div class="form-group" style="display: flex; gap: 8px;">
          <input type="text" id="new-keyword" class="form-input" placeholder="Enter a keyword..." onkeypress="if(event.key === 'Enter') KeywordsPage.addKeyword()">
          <button class="btn btn-primary" onclick="KeywordsPage.addKeyword()">Add</button>
        </div>
        
        <h3 class="mt-16">Active Keywords</h3>
        <div id="keywords-list"><div class="loading-spinner-sm"></div></div>
      </div>
    `;
    
    this.loadKeywords();
  },
  
  async loadKeywords() {
    const el = document.getElementById('keywords-list');
    if (!el) return;
    
    try {
      const res = await API.getKeywords(AppState.currentProject.id);
      const keywords = res.data || [];
      
      if (keywords.length === 0) {
        el.innerHTML = '<p class="text-secondary">No keywords added yet.</p>';
        return;
      }
      
      el.innerHTML = `
        <div class="chips-row">
          ${keywords.map(kw => `
            <span class="keyword-chip" style="display:inline-flex; align-items:center; gap:4px; font-size:14px; padding: 4px 8px; border-radius:16px; background:#e0e0e0; margin-right:8px; margin-bottom:8px;">
              ${escapeHtml(kw.keyword)}
              <span style="cursor:pointer; font-weight:bold; color:red;" onclick="KeywordsPage.deleteKeyword(${kw.id})">×</span>
            </span>
          `).join('')}
        </div>
      `;
    } catch (err) {
      el.innerHTML = `<p class="text-secondary">Error loading keywords: ${escapeHtml(err.message)}</p>`;
    }
  },
  
  async addKeyword() {
    const input = document.getElementById('new-keyword');
    const keyword = input?.value?.trim();
    if (!keyword) return;
    
    try {
      await API.addKeyword(AppState.currentProject.id, keyword);
      input.value = '';
      Toast.success('Keyword added');
      this.loadKeywords();
    } catch (err) {
      Toast.error(err.message);
    }
  },
  
  async deleteKeyword(id) {
    try {
      await API.deleteKeyword(id);
      Toast.success('Keyword deleted');
      this.loadKeywords();
    } catch (err) {
      Toast.error(err.message);
    }
  }
};
