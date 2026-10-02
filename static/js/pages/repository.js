const RepositoryPage = {
  currentPage: 1,
  currentFilters: {},
  
  async render(container) {
    if (!AppState.currentProject) {
      container.innerHTML = renderNoProject('Repository');
      return;
    }
    
    // Fetch topics and competitors for filter dropdowns
    const [topicsRes, compsRes] = await Promise.all([
      API.getTopics(AppState.currentProject.id).catch(() => ({data:[]})),
      API.getCompetitors(AppState.currentProject.id).catch(() => ({data:[]}))
    ]);
    const topics = topicsRes.data || [];
    const competitors = compsRes.data || [];
    
    container.innerHTML = `
      <div class="repository-page">
        <div class="page-header">
          <h2>🗄️ Post Repository</h2>
          <p class="text-secondary">Browse all collected competitor Google Maps posts</p>
        </div>
        
        <!-- Filter Bar -->
        <div class="card filter-bar">
          <div class="filter-row">
            <div class="form-group">
              <input type="text" id="filter-q" class="form-input" placeholder="Search posts...">
            </div>
            <div class="form-group">
              <select id="filter-competitor" class="form-select">
                <option value="">All Competitors</option>
                ${competitors.map(c => `<option value="${c.id}">${escapeHtml(c.name)}</option>`).join('')}
              </select>
            </div>
            <div class="form-group">
              <select id="filter-topic" class="form-select">
                <option value="">All Topics</option>
                ${topics.map(t => `<option value="${escapeHtml(t)}">${escapeHtml(t)}</option>`).join('')}
              </select>
            </div>
            <div class="form-group">
              <input type="text" id="filter-keyword" class="form-input" placeholder="Keyword...">
            </div>
            <div class="form-group">
              <input type="date" id="filter-date-from" class="form-input" title="Published from">
            </div>
            <div class="form-group">
              <input type="date" id="filter-date-to" class="form-input" placeholder="To">
            </div>
            <div class="filter-actions">
              <button class="btn btn-primary" onclick="RepositoryPage.applyFilters()">Apply</button>
              <button class="btn btn-secondary" onclick="RepositoryPage.clearFilters()">Clear</button>
            </div>
          </div>
        </div>
        
        <!-- Posts Grid -->
        <div id="posts-container"><div class="loading-page"><div class="loading-spinner"></div></div></div>
        
        <!-- Pagination -->
        <div id="pagination-container" class="pagination"></div>
      </div>
    `;
    
    this.currentPage = 1;
    this.loadPosts();
  },
  
  applyFilters() {
    this.currentFilters = {
      q: document.getElementById('filter-q')?.value || '',
      competitor_id: document.getElementById('filter-competitor')?.value || '',
      topic: document.getElementById('filter-topic')?.value || '',
      keyword: document.getElementById('filter-keyword')?.value || '',
      date_from: document.getElementById('filter-date-from')?.value || '',
      date_to: document.getElementById('filter-date-to')?.value || ''
    };
    // Remove empty keys
    Object.keys(this.currentFilters).forEach(k => { if (!this.currentFilters[k]) delete this.currentFilters[k]; });
    this.currentPage = 1;
    this.loadPosts();
  },
  
  clearFilters() {
    this.currentFilters = {};
    this.currentPage = 1;
    ['filter-q','filter-competitor','filter-topic','filter-keyword','filter-date-from','filter-date-to'].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.value = '';
    });
    this.loadPosts();
  },
  
  async loadPosts() {
    const container = document.getElementById('posts-container');
    if (!container) return;
    container.innerHTML = '<div class="loading-page"><div class="loading-spinner"></div></div>';
    
    try {
      const params = { ...this.currentFilters, page: this.currentPage };
      const res = await API.getPosts(AppState.currentProject.id, params);
      const { posts, total, pages, current_page } = res.data;
      
      if (posts.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">🗄️</div>
            <h3>No Posts Found</h3>
            <p>No posts match your filters. Try scraping some competitors first.</p>
          </div>
        `;
      } else {
        container.innerHTML = `
          <div class="post-grid">
            ${posts.map(post => this.renderPostCard(post)).join('')}
          </div>
        `;
      }
      
      this.renderPagination(pages, current_page, total);
    } catch (err) {
      container.innerHTML = `<div class="empty-state"><div class="empty-icon">❌</div><h3>Failed to load</h3><p>${escapeHtml(err.message)}</p></div>`;
    }
  },
  
  renderPostCard(post) {
    const images = Array.isArray(post.images) ? post.images : [];
    const keywords = Array.isArray(post.ai_keywords) ? post.ai_keywords : [];
    const topicClass = post.ai_main_topic ? 'topic-' + (post.ai_main_topic.toLowerCase().replace(/[^a-z]/g, '-').substring(0,20)) : '';
    
    return `
      <div class="post-card" onclick="RepositoryPage.showPostDetail(${post.id})">
        <div class="post-card-header">
          <span class="competitor-badge">${escapeHtml(post.competitor_name || '-')}</span>
          ${post.ai_main_topic ? `<span class="topic-chip ${topicClass}">${escapeHtml(post.ai_main_topic)}</span>` : ''}
        </div>
        ${images.length > 0 ? `
          <div class="post-images">
            ${images.slice(0,2).map(img => `<img src="/${img}" class="post-thumb" onclick="event.stopPropagation();openLightbox('/${img}')" alt="Post image">`).join('')}
          </div>
        ` : ''}
        <div class="post-text" onclick="event.stopPropagation();this.classList.toggle('expanded')">${escapeHtml(post.post_text || '')}</div>
        <div class="post-meta">
          <span class="text-secondary text-sm">${formatDate(post.published_date || post.scrape_date)}</span>
          ${post.call_to_action ? `<span class="cta-chip">${escapeHtml(post.call_to_action)}</span>` : ''}
        </div>
        ${keywords.length > 0 ? `
          <div class="post-keywords">
            ${keywords.slice(0,3).map(kw => `<span class="keyword-chip">${escapeHtml(kw)}</span>`).join('')}
          </div>
        ` : ''}
        ${post.ai_content_type ? `<div class="post-footer"><span class="content-type-chip">${escapeHtml(post.ai_content_type)}</span></div>` : ''}
      </div>
    `;
  },
  
  showPostDetail(postId) {
    API.getPost(postId).then(res => {
      const post = res.data;
      const images = Array.isArray(post.images) ? post.images : [];
      const keywords = Array.isArray(post.ai_keywords) ? post.ai_keywords : [];
      Modal.open(`Post from ${escapeHtml(post.competitor_name || 'Unknown')}`, `
        <div class="post-detail">
          ${images.length > 0 ? `<div class="post-images-large">${images.map(img => `<img src="/${img}" onclick="openLightbox('/${img}')" class="post-detail-img" alt="">`).join('')}</div>` : ''}
          <div class="detail-section">
            <label class="form-label">Post Text</label>
            <p class="post-full-text">${escapeHtml(post.post_text || '')}</p>
          </div>
          <div class="detail-grid">
            <div><label class="form-label">Published</label><p>${formatDate(post.published_date)}</p></div>
            <div><label class="form-label">Scraped</label><p>${formatDate(post.scrape_date)}</p></div>
            <div><label class="form-label">AI Topic</label><p>${escapeHtml(post.ai_main_topic || '-')}</p></div>
            <div><label class="form-label">Content Type</label><p>${escapeHtml(post.ai_content_type || '-')}</p></div>
            <div><label class="form-label">CTA</label><p>${escapeHtml(post.ai_cta || post.call_to_action || '-')}</p></div>
            <div><label class="form-label">Offer Pattern</label><p>${escapeHtml(post.ai_offer_pattern || '-')}</p></div>
          </div>
          ${keywords.length > 0 ? `
            <div class="detail-section">
              <label class="form-label">AI Keywords</label>
              <div class="chips-row">${keywords.map(k => `<span class="keyword-chip">${escapeHtml(k)}</span>`).join('')}</div>
            </div>
          ` : ''}
          ${post.post_url ? `<div class="detail-section"><label class="form-label">Post URL</label><a href="${escapeHtml(post.post_url)}" target="_blank" rel="noopener" class="link">${escapeHtml(post.post_url)}</a></div>` : ''}
          ${post.source_url ? `<div class="detail-section"><label class="form-label">Google Maps Profile</label><a href="${escapeHtml(post.source_url)}" target="_blank" rel="noopener" class="link">${escapeHtml(post.source_url)}</a></div>` : ''}
          <div class="detail-section">
            <label class="form-label">Scraping History</label>
            <p class="text-secondary text-sm">${post.collected_in_job ? `First collected in scrape job #${post.collected_in_job.id} on ${formatDate(post.collected_in_job.started_at)}. ` : `First collected ${formatDate(post.scrape_date)}. `}Later scrapes skip this post as a duplicate (fingerprint <code>${escapeHtml((post.fingerprint || '').slice(0, 12))}</code>).</p>
          </div>
          ${post.ai_sub_topic ? `<div class="detail-section"><label class="form-label">Sub-Topic</label><p>${escapeHtml(post.ai_sub_topic)}</p></div>` : ''}
        </div>
      `);
    }).catch(err => Toast.error(err.message));
  },
  
  renderPagination(pages, current, total) {
    const el = document.getElementById('pagination-container');
    if (!el || pages <= 1) { if(el) el.innerHTML = ''; return; }
    
    let html = `<span class="text-secondary">${total} posts</span>`;
    if (current > 1) html += `<button class="btn btn-secondary btn-sm" onclick="RepositoryPage.goToPage(${current-1})">← Prev</button>`;
    
    for (let i = Math.max(1, current-2); i <= Math.min(pages, current+2); i++) {
      html += `<button class="btn ${i === current ? 'btn-primary' : 'btn-secondary'} btn-sm" onclick="RepositoryPage.goToPage(${i})">${i}</button>`;
    }
    
    if (current < pages) html += `<button class="btn btn-secondary btn-sm" onclick="RepositoryPage.goToPage(${current+1})">Next →</button>`;
    el.innerHTML = html;
  },
  
  goToPage(page) {
    this.currentPage = page;
    this.loadPosts();
    document.querySelector('.repository-page')?.scrollTo(0, 0);
  }
};
