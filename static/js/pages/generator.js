const GeneratorPage = {
  _ideas: [],
  _tab: 'new',
  
  async render(container) {
    if (!AppState.currentProject) {
      container.innerHTML = renderNoProject('Content Generator');
      return;
    }
    
    const statsRes = await API.getIdeasStats(AppState.currentProject.id).catch(() => ({data:{total:0,used:0,by_provider:{}}}));
    const stats = statsRes.data;
    
    container.innerHTML = `
      <div class="generator-page">
        <div class="page-header">
          <h2>✨ Content Generator</h2>
          <p class="text-secondary">Generate unique Google Maps update ideas powered by AI competitor analysis</p>
        </div>
        
        <div class="generator-control card">
          <div class="generate-form">
            <div class="count-control">
              <button class="btn btn-icon" onclick="GeneratorPage.adjustCount(-1)">−</button>
              <input type="number" id="idea-count" class="count-input" value="5" min="1" max="50">
              <button class="btn btn-icon" onclick="GeneratorPage.adjustCount(1)">+</button>
            </div>
            <div class="generate-info">
              <span class="generate-label">ideas to generate</span>
              ${stats.total > 0 ? `<span class="duplicate-notice">🔄 ${stats.total} ideas already exist — generating unique new content only</span>` : ''}
            </div>
            <button class="btn btn-primary btn-lg" id="generate-btn" onclick="GeneratorPage.generate()">
              ✨ Generate Ideas
            </button>
          </div>
          <div class="generate-stats">
            <span class="stat-chip">📝 ${stats.total} Total Ideas</span>
            <span class="stat-chip">✅ ${stats.used} Used</span>
            <span class="stat-chip">🤖 ${stats.by_provider?.gemini || 0} Gemini • ${stats.by_provider?.grok || 0} Grok</span>
          </div>
        </div>
        
        <div class="tab-bar">
          <button class="tab-btn ${this._tab === 'new' ? 'active' : ''}" onclick="GeneratorPage.switchTab('new')">New Ideas</button>
          <button class="tab-btn ${this._tab === 'history' ? 'active' : ''}" onclick="GeneratorPage.switchTab('history')">History</button>
        </div>
        
        <div id="ideas-container">
          <div class="loading-page"><div class="loading-spinner"></div></div>
        </div>
      </div>
    `;
    
    this.loadIdeas();
  },
  
  adjustCount(delta) {
    const input = document.getElementById('idea-count');
    if (!input) return;
    const val = Math.min(50, Math.max(1, (parseInt(input.value) || 5) + delta));
    input.value = val;
  },
  
  switchTab(tab) {
    this._tab = tab;
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.toggle('active', b.textContent.toLowerCase().startsWith(tab)));
    this.renderIdeas();
  },
  
  async generate() {
    const count = parseInt(document.getElementById('idea-count')?.value) || 5;
    const btn = document.getElementById('generate-btn');
    if (btn) { btn.disabled = true; btn.innerHTML = '<span class="loading-spinner-sm"></span> Generating...'; }
    
    try {
      const res = await API.generateIdeas(AppState.currentProject.id, count);
      const ideas = res.data?.ideas || [];
      const warnings = res.data?.warnings || [];
      if (ideas.length === 0) Toast.warning(warnings[0] || 'No new unique ideas could be generated.');
      else Toast.success(`Generated ${ideas.length} of ${res.data.requested} requested ideas (${res.data.provider})`);
      if (ideas.length > 0 && warnings.length) Toast.warning(warnings[0]);
      this._tab = 'new';
      await this.loadIdeas();
    } catch (err) {
      Toast.error(err.message || 'Generation failed. Check your AI API key.');
    } finally {
      if (btn) { btn.disabled = false; btn.innerHTML = '✨ Generate Ideas'; }
    }
  },
  
  async loadIdeas() {
    try {
      const res = await API.getIdeas(AppState.currentProject.id);
      this._ideas = res.data?.ideas || [];
      this.renderIdeas();
    } catch (err) {
      document.getElementById('ideas-container').innerHTML = `<p class="text-secondary">${escapeHtml(err.message)}</p>`;
    }
  },
  
  renderIdeas() {
    const container = document.getElementById('ideas-container');
    if (!container) return;
    
    const filtered = this._tab === 'history' ? this._ideas.filter(i => i.is_used) : this._ideas.filter(i => !i.is_used);
    
    if (filtered.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">✨</div>
          <h3>${this._tab === 'new' ? 'No Ideas Yet' : 'No Used Ideas'}</h3>
          <p>${this._tab === 'new' ? 'Click "Generate Ideas" to create your first batch of AI-powered content ideas!' : 'Mark ideas as used to track your content calendar.'}</p>
        </div>
      `;
      return;
    }
    
    container.innerHTML = `
      <div class="ideas-grid">
        ${filtered.map(idea => this.renderIdeaCard(idea)).join('')}
      </div>
    `;
  },
  
  renderIdeaCard(idea) {
    const keywords = Array.isArray(idea.keywords) ? idea.keywords : [];
    return `
      <div class="idea-card ${idea.is_used ? 'idea-used' : ''}" id="idea-${idea.id}">
        <div class="idea-card-header">
          <h4>${escapeHtml(idea.topic)}</h4>
          <span class="ai-provider-pill">${idea.ai_provider === 'gemini' ? '🔷 Gemini' : idea.ai_provider === 'grok' ? '⚫ Grok' : idea.ai_provider === 'demo' ? '📦 Demo' : '🔧 Template'}</span>
        </div>
        <div class="idea-card-body">
          <div class="form-group">
            <label class="form-label">Update Copy</label>
            <textarea class="form-textarea idea-copy" rows="5" id="copy-${idea.id}">${escapeHtml(idea.update_copy || '')}</textarea>
          </div>
          ${keywords.length > 0 ? `
            <div class="idea-keywords">
              <label class="form-label">Keywords</label>
              <div class="chips-row">${keywords.map(k => `<span class="keyword-chip">${escapeHtml(k)}</span>`).join('')}</div>
            </div>
          ` : ''}
          ${idea.call_to_action ? `
            <div class="form-group">
              <label class="form-label">Call to Action</label>
              <p class="idea-cta">${escapeHtml(idea.call_to_action)}</p>
            </div>
          ` : ''}
          ${idea.image_concept ? `
            <div class="form-group">
              <label class="form-label">📷 Image Concept</label>
              <p class="idea-image-concept">${escapeHtml(idea.image_concept)}</p>
            </div>
          ` : ''}
        </div>
        <div class="idea-card-footer">
          <span class="text-secondary text-sm">${formatRelativeTime(idea.generated_at)}</span>
          <div class="idea-actions">
            <button class="btn btn-sm btn-secondary" onclick="GeneratorPage.copyIdea(${idea.id})">📋 Copy</button>
            <button class="btn btn-sm ${idea.is_used ? 'btn-secondary' : 'btn-success'}" onclick="GeneratorPage.toggleUsed(${idea.id}, ${!idea.is_used})">
              ${idea.is_used ? '↩ Unmark' : '✅ Mark Used'}
            </button>
            <button class="btn btn-sm btn-danger" onclick="GeneratorPage.deleteIdea(${idea.id})">🗑</button>
          </div>
        </div>
      </div>
    `;
  },
  
  copyIdea(id) {
    const textarea = document.getElementById(`copy-${id}`);
    if (textarea) {
      navigator.clipboard.writeText(textarea.value).then(() => Toast.success('Copied to clipboard!')).catch(() => Toast.error('Copy failed'));
    }
  },
  
  async toggleUsed(id, isUsed) {
    try {
      await API.updateIdea(id, {is_used: isUsed});
      Toast.success(isUsed ? 'Marked as used' : 'Unmarked');
      await this.loadIdeas();
    } catch (err) {
      Toast.error(err.message);
    }
  },
  
  deleteIdea(id) {
    Modal.confirm('Delete Idea', 'Delete this generated idea? This cannot be undone.', async () => {
      try {
        await API.deleteIdea(id);
        Toast.success('Idea deleted');
        await this.loadIdeas();
      } catch (err) {
        Toast.error(err.message);
      }
    }, 'Delete', true);
  }
};
