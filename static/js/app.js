// Global state
const AppState = {
  currentPage: 'dashboard',
  currentProject: null,
  projects: [],
  sidebarOpen: false,
};

// Page registry
const Pages = {
  dashboard: typeof DashboardPage !== 'undefined' ? DashboardPage : null,
  projects: typeof ProjectsPage !== 'undefined' ? ProjectsPage : null,
  competitors: typeof CompetitorsPage !== 'undefined' ? CompetitorsPage : null,
  keywords: typeof KeywordsPage !== 'undefined' ? KeywordsPage : null,
  scraping: typeof ScrapingPage !== 'undefined' ? ScrapingPage : null,
  repository: typeof RepositoryPage !== 'undefined' ? RepositoryPage : null,
  analysis: typeof AnalysisPage !== 'undefined' ? AnalysisPage : null,
  trends: typeof TrendsPage !== 'undefined' ? TrendsPage : null,
  generator: typeof GeneratorPage !== 'undefined' ? GeneratorPage : null,
};

const PAGE_TITLES = {
  dashboard: 'Dashboard',
  projects: 'Projects',
  competitors: 'Competitors',
  keywords: 'Keywords',
  scraping: 'Scraping',
  repository: 'Repository',
  analysis: 'AI Analysis',
  trends: 'Trends',
  generator: 'Content Generator',
};

async function navigateTo(page) {
  Charts.destroyAll();
  AppState.currentPage = page;
  
  // Update nav links
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.toggle('active', link.dataset.page === page);
  });
  
  // Update page title
  document.getElementById('page-title').textContent = PAGE_TITLES[page] || page;
  
  // Render page
  const container = document.getElementById('page-container');
  const PageObj = Pages[page];
  if (PageObj && typeof PageObj.render === 'function') {
    try {
      await PageObj.render(container);
    } catch (err) {
      container.innerHTML = `<div class="empty-state"><div class="empty-icon">❌</div><h3>Page Error</h3><p>${escapeHtml(err.message)}</p></div>`;
    }
  } else {
    container.innerHTML = `<div class="empty-state"><div class="empty-icon">🚧</div><h3>Coming Soon</h3><p>This page is under construction.</p></div>`;
  }
  
  // Close mobile sidebar
  if (window.innerWidth <= 768) {
    document.getElementById('sidebar').classList.remove('sidebar-open');
  }
}

async function loadProjects() {
  try {
    const res = await API.getProjects();
    AppState.projects = res.data || [];
    updateProjectSelector();
    if (AppState.projects.length > 0 && !AppState.currentProject) {
      await selectProject(AppState.projects[0].id);
    }
  } catch (err) {
    console.error('Failed to load projects:', err);
  }
}

function updateProjectSelector() {
  const sel = document.getElementById('project-select');
  const currentId = AppState.currentProject?.id;
  sel.innerHTML = '<option value="">Select a project...</option>';
  AppState.projects.forEach(p => {
    const opt = document.createElement('option');
    opt.value = p.id;
    opt.textContent = p.name;
    if (p.id === currentId) opt.selected = true;
    sel.appendChild(opt);
  });
}

async function selectProject(projectId) {
  const id = parseInt(projectId);
  if (!id) {
    AppState.currentProject = null;
    document.getElementById('project-badge').textContent = 'No project selected';
    return;
  }
  const project = AppState.projects.find(p => p.id === id);
  AppState.currentProject = project || null;
  const badge = document.getElementById('project-badge');
  badge.textContent = project ? project.name : 'No project selected';
  // Re-render current page
  await navigateTo(AppState.currentPage);
}

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  sidebar.classList.toggle('sidebar-open');
}

// Utility functions used across all pages
function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#x27;');
}

function formatDate(dateStr) {
  if (!dateStr) return 'N/A';
  try {
    return new Date(dateStr).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
  } catch { return dateStr; }
}

function formatRelativeTime(dateStr) {
  if (!dateStr) return 'N/A';
  try {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  } catch { return dateStr; }
}

function truncate(str, len = 150) {
  if (!str) return '';
  return str.length > len ? str.substring(0, len) + '...' : str;
}

function animateCount(element, target, duration = 1000) {
  const start = parseInt(element.textContent) || 0;
  const range = target - start;
  const startTime = performance.now();
  function update(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    element.textContent = Math.round(start + range * eased);
    if (progress < 1) requestAnimationFrame(update);
  }
  requestAnimationFrame(update);
}

function openLightbox(src) {
  const lb = document.getElementById('lightbox');
  const img = document.getElementById('lightbox-img');
  img.src = src;
  lb.classList.remove('hidden');
}

function closeLightbox() {
  document.getElementById('lightbox').classList.add('hidden');
}

// Init
document.addEventListener('DOMContentLoaded', async () => {
  // Nav links
  document.querySelectorAll('.nav-link[data-page]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      navigateTo(link.dataset.page);
    });
  });
  
  // Project selector change
  document.getElementById('project-select').addEventListener('change', (e) => {
    selectProject(e.target.value);
  });
  
  // Load projects and go to dashboard
  await loadProjects();
  await navigateTo('dashboard');
});
