const API_BASE = '/api';

async function apiFetch(path, options = {}) {
  const defaultHeaders = { 'Content-Type': 'application/json' };
  const config = {
    ...options,
    headers: { ...defaultHeaders, ...(options.headers || {}) }
  };
  const res = await fetch(API_BASE + path, config);
  const data = await res.json();
  if (!res.ok || data.success === false) {
    throw new Error(data.message || `HTTP ${res.status}`);
  }
  return data;
}

const API = {
  // Projects
  getProjects: () => apiFetch('/projects'),
  createProject: (data) => apiFetch('/projects', { method: 'POST', body: JSON.stringify(data) }),
  getProject: (id) => apiFetch(`/projects/${id}`),
  updateProject: (id, data) => apiFetch(`/projects/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteProject: (id) => apiFetch(`/projects/${id}`, { method: 'DELETE' }),
  getProjectStats: (id) => apiFetch(`/projects/${id}/stats`),

  // Competitors
  getCompetitors: (projectId) => apiFetch(`/competitors/project/${projectId}`),
  addCompetitor: (projectId, data) => apiFetch(`/competitors/project/${projectId}`, { method: 'POST', body: JSON.stringify(data) }),
  updateCompetitor: (id, data) => apiFetch(`/competitors/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteCompetitor: (id) => apiFetch(`/competitors/${id}`, { method: 'DELETE' }),
  getCompetitorPosts: (id) => apiFetch(`/competitors/${id}/posts`),

  // Keywords
  getKeywords: (projectId) => apiFetch(`/keywords/project/${projectId}`),
  addKeyword: (projectId, keyword) => apiFetch(`/keywords/project/${projectId}`, { method: 'POST', body: JSON.stringify({ keyword }) }),
  deleteKeyword: (id) => apiFetch(`/keywords/${id}`, { method: 'DELETE' }),

  // Scraping
  startScrape: (projectId, competitorIds) => apiFetch('/scraping/start', { method: 'POST', body: JSON.stringify({ project_id: projectId, competitor_ids: competitorIds }) }),
  getJobStatus: (jobId) => apiFetch(`/scraping/job/${jobId}/status`),
  resumeJob: (jobId) => apiFetch(`/scraping/job/${jobId}/resume`, { method: 'POST' }),
  getScrapeJobs: (projectId) => apiFetch(`/scraping/project/${projectId}/jobs`),
  getScrapeLogs: (projectId) => apiFetch(`/scraping/project/${projectId}/logs`),

  // Posts
  getPosts: (projectId, params = {}) => {
    const q = new URLSearchParams(params).toString();
    return apiFetch(`/posts/project/${projectId}?${q}`);
  },
  getPost: (id) => apiFetch(`/posts/${id}`),
  getTopics: (projectId) => apiFetch(`/posts/project/${projectId}/topics`),

  // Analysis
  runAnalysis: (projectId) => apiFetch(`/analysis/project/${projectId}/run`, { method: 'POST' }),
  getAnalysisStatus: (projectId) => apiFetch(`/analysis/project/${projectId}/status`),
  getAnalysisResults: (projectId, page = 1) => apiFetch(`/analysis/project/${projectId}/results?page=${page}`),

  // Trends
  getTrends: (projectId) => apiFetch(`/trends/project/${projectId}`),
  calculateTrends: (projectId) => apiFetch(`/trends/project/${projectId}/calculate`, { method: 'POST' }),
  getTrendKeywords: (projectId) => apiFetch(`/trends/project/${projectId}/keywords`),
  getPatterns: (projectId) => apiFetch(`/trends/project/${projectId}/patterns`),

  // Generator
  generateIdeas: (projectId, count) => apiFetch(`/generator/project/${projectId}/generate`, { method: 'POST', body: JSON.stringify({ count }) }),
  getIdeas: (projectId) => apiFetch(`/generator/project/${projectId}/ideas?per_page=200`),
  updateIdea: (id, data) => apiFetch(`/generator/idea/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  deleteIdea: (id) => apiFetch(`/generator/idea/${id}`, { method: 'DELETE' }),
  getIdeasStats: (projectId) => apiFetch(`/generator/project/${projectId}/ideas/stats`),
};
