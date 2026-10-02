const ProjectsPage = {
  async render(container) {
    // Show loading skeleton
    container.innerHTML = '<div class="loading-page"><div class="loading-spinner"></div></div>';
    
    try {
      const res = await API.getProjects();
      const projects = res.data || [];
      
      container.innerHTML = `
        <div class="page-header">
          <div>
            <h2>Projects</h2>
            <p class="text-secondary">Manage your competitor intelligence projects</p>
          </div>
          <button class="btn btn-primary" onclick="ProjectsPage.showCreateModal()">+ New Project</button>
        </div>
        ${projects.length === 0 ? `
          <div class="empty-state">
            <div class="empty-icon">📁</div>
            <h3>No Projects Yet</h3>
            <p>Create your first project to start tracking competitor activity.</p>
            <button class="btn btn-primary" onclick="ProjectsPage.showCreateModal()">Create Project</button>
          </div>
        ` : `
          <div class="cards-grid">
            ${projects.map(p => ProjectsPage.renderCard(p)).join('')}
          </div>
        `}
      `;
    } catch (err) {
      Toast.error(err.message);
    }
  },
  
  renderCard(p) {
    return `
      <div class="card project-card" onclick="ProjectsPage.selectProject(${p.id})" style="cursor:pointer">
        <div class="project-card-header">
          <div class="project-card-icon">📁</div>
          <div>
            <h3>${escapeHtml(p.name)}</h3>
            <div class="text-secondary">${escapeHtml(p.own_profile_name || 'No profile set')}</div>
          </div>
        </div>
        <div class="project-stats">
          <div class="project-stat">
            <span class="stat-num">${p.competitor_count || 0}</span>
            <span class="stat-lbl">Competitors</span>
          </div>
          <div class="project-stat">
            <span class="stat-num">${p.post_count || 0}</span>
            <span class="stat-lbl">Posts</span>
          </div>
        </div>
        <div class="project-card-footer">
          <span class="text-secondary text-sm">${formatDate(p.created_at)}</span>
          <div class="project-actions" onclick="event.stopPropagation()">
            <button class="btn btn-sm btn-secondary" onclick="ProjectsPage.showEditModal(${JSON.stringify(p).replace(/"/g, '&quot;')})">Edit</button>
            <button class="btn btn-sm btn-danger" onclick="ProjectsPage.deleteProject(${p.id})">Delete</button>
          </div>
        </div>
      </div>
    `;
  },
  
  async selectProject(id) {
    document.getElementById('project-select').value = id;
    await selectProject(id);
    navigateTo('dashboard');
  },
  
  showCreateModal() {
    Modal.open('Create New Project', `
      <form id="project-form">
        <div class="form-group">
          <label class="form-label">Project Name *</label>
          <input type="text" id="proj-name" class="form-input" placeholder="e.g. Luxe Salon Intelligence" required>
        </div>
        <div class="form-group">
          <label class="form-label">Your Business Name</label>
          <input type="text" id="proj-own" class="form-input" placeholder="e.g. Luxe Salon, Kharghar">
        </div>
        <div class="form-group">
          <label class="form-label">Your Google Maps URL</label>
          <input type="url" id="proj-url" class="form-input" placeholder="https://maps.google.com/...">
        </div>
        <div class="form-group">
          <label class="form-label">Description</label>
          <textarea id="proj-desc" class="form-textarea" rows="3" placeholder="Brief description of this project"></textarea>
        </div>
      </form>
    `, `
      <button class="btn btn-secondary" onclick="Modal.close()">Cancel</button>
      <button class="btn btn-primary" onclick="ProjectsPage.createProject()">Create Project</button>
    `);
  },
  
  showEditModal(p) {
    Modal.open('Edit Project', `
      <form id="project-form">
        <input type="hidden" id="proj-id" value="${p.id}">
        <div class="form-group">
          <label class="form-label">Project Name *</label>
          <input type="text" id="proj-name" class="form-input" value="${escapeHtml(p.name)}" required>
        </div>
        <div class="form-group">
          <label class="form-label">Your Business Name</label>
          <input type="text" id="proj-own" class="form-input" value="${escapeHtml(p.own_profile_name || '')}">
        </div>
        <div class="form-group">
          <label class="form-label">Your Google Maps URL</label>
          <input type="url" id="proj-url" class="form-input" value="${escapeHtml(p.own_profile_url || '')}">
        </div>
        <div class="form-group">
          <label class="form-label">Description</label>
          <textarea id="proj-desc" class="form-textarea" rows="3">${escapeHtml(p.description || '')}</textarea>
        </div>
      </form>
    `, `
      <button class="btn btn-secondary" onclick="Modal.close()">Cancel</button>
      <button class="btn btn-primary" onclick="ProjectsPage.updateProject()">Save Changes</button>
    `);
  },
  
  async createProject() {
    const name = document.getElementById('proj-name')?.value?.trim();
    if (!name) { Toast.error('Project name is required'); return; }
    try {
      await API.createProject({
        name,
        own_profile_name: document.getElementById('proj-own')?.value?.trim(),
        own_profile_url: document.getElementById('proj-url')?.value?.trim(),
        description: document.getElementById('proj-desc')?.value?.trim()
      });
      Modal.close();
      Toast.success('Project created!');
      await loadProjects();
      this.render(document.getElementById('page-container'));
    } catch (err) {
      Toast.error(err.message);
    }
  },
  
  async updateProject() {
    const id = document.getElementById('proj-id')?.value;
    const name = document.getElementById('proj-name')?.value?.trim();
    if (!name) { Toast.error('Project name is required'); return; }
    try {
      await API.updateProject(id, {
        name,
        own_profile_name: document.getElementById('proj-own')?.value?.trim(),
        own_profile_url: document.getElementById('proj-url')?.value?.trim(),
        description: document.getElementById('proj-desc')?.value?.trim()
      });
      Modal.close();
      Toast.success('Project updated!');
      await loadProjects();
      this.render(document.getElementById('page-container'));
    } catch (err) {
      Toast.error(err.message);
    }
  },
  
  deleteProject(id) {
    Modal.confirm('Delete Project', 'This will permanently delete the project and all its data. Are you sure?', async () => {
      try {
        await API.deleteProject(id);
        Toast.success('Project deleted');
        await loadProjects();
        ProjectsPage.render(document.getElementById('page-container'));
      } catch (err) {
        Toast.error(err.message);
      }
    }, 'Delete', true);
  }
};
