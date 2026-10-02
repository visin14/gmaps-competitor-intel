const DashboardPage = {
  async render(container) {
    if (!AppState.currentProject) {
      container.innerHTML = renderNoProject('Dashboard');
      return;
    }
    
    // Show skeleton first
    container.innerHTML = renderDashboardSkeleton();
    
    try {
      const [statsRes, jobsRes, competitorsRes] = await Promise.all([
        API.getProjectStats(AppState.currentProject.id),
        API.getScrapeJobs(AppState.currentProject.id).catch(() => ({ data: [] })),
        API.getCompetitors(AppState.currentProject.id).catch(() => ({ data: [] }))
      ]);
      const stats = statsRes.data;
      const jobs = jobsRes.data || [];
      const competitors = competitorsRes.data || [];
      const lastJob = jobs.length > 0 ? jobs[0] : null;
      
      // Build the greeting based on time of day
      const hour = new Date().getHours();
      const greeting = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';
      
      container.innerHTML = `
        <div class="dashboard">
          
          <!-- Hero Banner -->
          <div class="dash-hero">
            <div class="dash-hero-content">
              <div>
                <h1>${greeting}! 👋</h1>
                <p>Here's what's happening with <strong>${escapeHtml(AppState.currentProject.name)}</strong> today. Stay ahead of the competition.</p>
              </div>
              <div class="dash-hero-actions">
                <button class="btn btn-primary" onclick="navigateTo('scraping')">🔍 Scrape Now</button>
                <button class="btn btn-gradient" onclick="navigateTo('generator')">✨ Generate Ideas</button>
              </div>
            </div>
          </div>
          
          <!-- KPI Cards -->
          <div class="stats-grid">
            ${renderStatCard('Competitors', stats.competitor_count || 0, '🎯', 'purple')}
            ${renderStatCard('Total Posts', stats.total_posts || 0, '📝', 'cyan')}
            ${renderStatCard('New Posts', stats.new_posts_last_scrape || 0, '🆕', 'green')}
            ${renderStatCard('Duplicates Skipped', stats.duplicates_last_scrape || 0, '🔄', 'yellow')}
            ${renderStatCard('AI Analyzed', stats.analysis_count || 0, '🧠', 'blue')}
            ${renderStatCard('Failed Scrapes', stats.failed_scrapes || 0, '⚠️', 'yellow')}
            ${renderStatCard('Ideas Generated', stats.generated_count || 0, '💡', 'pink')}
          </div>
          <div class="card" style="margin-bottom:1.5rem">
            <h3 class="card-title">🕒 Last scraping activity: <span class="text-secondary">${stats.last_scrape_date ? formatRelativeTime(stats.last_scrape_date) : 'never'}</span>
              ${stats.manual_interventions ? ` · <span class="text-secondary">${stats.manual_interventions} manual verification(s) so far</span>` : ''}</h3>
            ${(stats.top_keywords || []).length ? `<div class="chips-row" style="margin-top:.5rem"><span class="text-secondary">Top keywords:</span> ${stats.top_keywords.map(k => `<span class="keyword-chip">${escapeHtml(k.keyword)} · ${k.count}</span>`).join('')}</div>` : ''}
          </div>
          
          <!-- Two Column Section -->
          <div class="dashboard-grid">
            
            <!-- Left: Top Topics Chart -->
            <div class="card">
              <h3 class="card-title">📊 Content Topics Breakdown</h3>
              ${stats.top_topics && stats.top_topics.length > 0 ? `
                <canvas id="dashboard-topics-donut" height="260"></canvas>
              ` : '<div class="empty-state" style="padding:2rem 0"><div class="empty-icon">📊</div><p class="text-secondary">Run AI Analysis to discover content topics.</p></div>'}
            </div>
            
            <!-- Right: Activity Feed -->
            <div class="card">
              <h3 class="card-title">⚡ Recent Activity</h3>
              <div class="activity-feed">
                ${lastJob ? `
                  <div class="activity-item">
                    <div class="activity-dot green"></div>
                    <div>
                      <div class="activity-text"><strong>Scrape job completed</strong> — ${lastJob.processed_competitors || 0} competitors processed</div>
                      <div class="activity-time">${formatRelativeTime(lastJob.started_at)}</div>
                    </div>
                  </div>
                ` : ''}
                ${stats.analysis_count > 0 ? `
                  <div class="activity-item">
                    <div class="activity-dot purple"></div>
                    <div>
                      <div class="activity-text"><strong>${stats.analysis_count} posts</strong> analyzed with AI</div>
                      <div class="activity-time">Up to date</div>
                    </div>
                  </div>
                ` : ''}
                ${stats.generated_count > 0 ? `
                  <div class="activity-item">
                    <div class="activity-dot blue"></div>
                    <div>
                      <div class="activity-text"><strong>${stats.generated_count} content ideas</strong> generated and ready</div>
                      <div class="activity-time">Available</div>
                    </div>
                  </div>
                ` : ''}
                ${competitors.length > 0 ? `
                  <div class="activity-item">
                    <div class="activity-dot yellow"></div>
                    <div>
                      <div class="activity-text"><strong>${competitors.length} competitors</strong> being tracked</div>
                      <div class="activity-time">Active</div>
                    </div>
                  </div>
                ` : ''}
                ${!lastJob && stats.analysis_count === 0 && stats.generated_count === 0 ? `
                  <div class="empty-state" style="padding: 2rem 0">
                    <div class="empty-icon">🚀</div>
                    <p class="text-secondary">Get started by scraping your competitors!</p>
                  </div>
                ` : ''}
              </div>
            </div>
          </div>
          
          <!-- Second Row: Trend Bars + Scrape History -->
          <div class="dashboard-grid">
            
            <!-- Topic Trend Bars -->
            <div class="card">
              <h3 class="card-title">📈 Top Trending Topics</h3>
              ${stats.top_topics && stats.top_topics.length > 0 ? `
                <div class="dash-trend-bars" id="dash-trend-bars">
                  ${stats.top_topics.map((t, i) => {
                    const maxCount = Math.max(...stats.top_topics.map(x => x.count));
                    const pct = maxCount > 0 ? (t.count / maxCount * 100) : 0;
                    return `
                      <div class="trend-row">
                        <div class="trend-topic">${escapeHtml(t.topic)}</div>
                        <div class="trend-bar-bg">
                          <div class="trend-fill" style="width: 0%" data-width="${pct}%"></div>
                        </div>
                        <div class="trend-count">${t.count}</div>
                      </div>
                    `;
                  }).join('')}
                </div>
              ` : '<div class="empty-state" style="padding:2rem 0"><div class="empty-icon">📈</div><p class="text-secondary">Calculate trends to see topic breakdown.</p></div>'}
            </div>
            
            <!-- Scrape Jobs History -->
            <div class="card">
              <h3 class="card-title">🕒 Scrape History</h3>
              ${jobs.length > 0 ? `
                <div class="recent-jobs">
                  ${jobs.slice(0, 6).map(job => `
                    <div class="job-item">
                      <div class="job-info">
                        <span class="badge badge-${job.status}">${job.status}</span>
                        <span class="job-time">${formatRelativeTime(job.started_at)}</span>
                      </div>
                      <div class="job-stats">
                        ${job.total_competitors || 0} competitor${(job.total_competitors || 0) !== 1 ? 's' : ''}
                      </div>
                    </div>
                  `).join('')}
                </div>
              ` : '<div class="empty-state" style="padding:2rem 0"><div class="empty-icon">🕒</div><p class="text-secondary">No scrape jobs recorded yet.</p></div>'}
            </div>
          </div>
          
          <!-- Quick Actions -->
          <div class="quick-actions">
            <h3>🚀 Quick Actions</h3>
            <div class="quick-actions-grid">
              <button class="quick-action-card" onclick="navigateTo('competitors')">
                <span class="qa-icon">🎯</span>
                <span>Manage Competitors</span>
              </button>
              <button class="quick-action-card" onclick="navigateTo('repository')">
                <span class="qa-icon">🗄️</span>
                <span>Browse Repository</span>
              </button>
              <button class="quick-action-card" onclick="navigateTo('trends')">
                <span class="qa-icon">📈</span>
                <span>View Trends</span>
              </button>
              <button class="quick-action-card" onclick="navigateTo('analysis')">
                <span class="qa-icon">🧠</span>
                <span>AI Analysis</span>
              </button>
            </div>
          </div>
        </div>
      `;
      
      // Animate stat numbers
      document.querySelectorAll('.stat-value[data-target]').forEach(el => {
        animateCount(el, parseInt(el.dataset.target));
      });
      
      // Render donut chart if data
      if (stats.top_topics && stats.top_topics.length > 0) {
        const labels = stats.top_topics.map(t => t.topic);
        const data = stats.top_topics.map(t => t.count);
        setTimeout(() => Charts.createDonut('dashboard-topics-donut', labels, data), 200);
      }
      
      // Animate trend bars
      setTimeout(() => {
        document.querySelectorAll('.trend-fill[data-width]').forEach(bar => {
          bar.style.width = bar.dataset.width;
        });
      }, 400);
      
    } catch (err) {
      container.innerHTML = `<div class="empty-state"><div class="empty-icon">❌</div><h3>Failed to load dashboard</h3><p>${escapeHtml(err.message)}</p></div>`;
    }
  }
};

function renderStatCard(label, value, icon, color) {
  return `
    <div class="stat-card stat-card-${color}">
      <div class="stat-icon">${icon}</div>
      <div class="stat-value" data-target="${value}">0</div>
      <div class="stat-label">${escapeHtml(label)}</div>
    </div>
  `;
}

function renderDashboardSkeleton() {
  return `
    <div class="dashboard">
      <div class="skeleton" style="height:160px; margin-bottom:2rem; border-radius: 1.5rem;"></div>
      <div class="stats-grid">
        ${Array(6).fill('<div class="skeleton" style="min-height:110px"></div>').join('')}
      </div>
      <div class="dashboard-grid">
        <div class="skeleton" style="min-height:300px"></div>
        <div class="skeleton" style="min-height:300px"></div>
      </div>
    </div>
  `;
}

function renderNoProject(page) {
  return `
    <div class="empty-state">
      <div class="empty-icon">📁</div>
      <h3>No Project Selected</h3>
      <p>Select an existing project or create a new one to use the ${escapeHtml(page)} page.</p>
      <button class="btn btn-primary" onclick="navigateTo('projects')">Go to Projects</button>
    </div>
  `;
}
