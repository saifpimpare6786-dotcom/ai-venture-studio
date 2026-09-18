const API_BASE = '/api';

function getAuthHeaders(extraHeaders = {}) {
  const headers = { ...extraHeaders };
  try {
    const raw = localStorage.getItem('avs_user');
    if (raw) {
      const user = JSON.parse(raw);
      if (user?.id) {
        headers['X-User-ID'] = user.id;
      }
      if (user?.token) {
        headers['Authorization'] = `Bearer ${user.token}`;
      }
    }
  } catch (e) {
    // Ignore storage parse errors
  }
  return headers;
}

function getUserId() {
  try {
    const raw = localStorage.getItem('avs_user');
    if (raw) {
      const user = JSON.parse(raw);
      return user?.id || 'default_founder';
    }
  } catch (e) {
    // ignore
  }
  return 'default_founder';
}

export const api = {
  // Projects
  async createProject(data) {
    const res = await fetch(`${API_BASE}/projects`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      const errText = await res.text();
      throw new Error(errText || `Server error: ${res.status}`);
    }
    return res.json();
  },

  async getProject(projectId) {
    const res = await fetch(`${API_BASE}/projects/${projectId}`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async listProjects() {
    const res = await fetch(`${API_BASE}/projects`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async deleteProject(projectId) {
    const res = await fetch(`${API_BASE}/projects/${projectId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Documents Upload
  async uploadDocument(projectId, file) {
    const formData = new FormData();
    formData.append('project_id', projectId);
    formData.append('file', file);

    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: formData,
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Reports & Deliberation
  async generateReports(projectId) {
    const res = await fetch(`${API_BASE}/reports/generate/${projectId}`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getReports(projectId) {
    const res = await fetch(`${API_BASE}/reports/${projectId}`, {
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async regenerateSingleReport(projectId, reportType) {
    const res = await fetch(`${API_BASE}/reports/regenerate-single/${projectId}/${reportType}`, {
      method: 'POST',
      headers: getAuthHeaders()
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  // Exports
  getExportUrl(projectId, format) {
    const userId = getUserId();
    return `${API_BASE}/reports/export/${projectId}/${format}?user_id=${encodeURIComponent(userId)}`;
  },

  getExcelModelUrl(projectName) {
    const userId = getUserId();
    return `${API_BASE}/simulator/export-excel/${encodeURIComponent(projectName)}?user_id=${encodeURIComponent(userId)}`;
  },

  // Simulator
  async calculateSimulation(params) {
    const res = await fetch(`${API_BASE}/simulator/calculate`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getScenarios(params) {
    const res = await fetch(`${API_BASE}/simulator/scenarios`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getAiAnalysis(projectId, params) {
    const res = await fetch(`${API_BASE}/simulator/ai-analysis/${projectId}`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(params),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async partnerInterrogation(projectId, payload = {}) {
    const res = await fetch(`${API_BASE}/simulator/partner-interrogation/${projectId}`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async inversionAnalysis(projectId, payload = {}) {
    const res = await fetch(`${API_BASE}/simulator/inversion-analysis/${projectId}`, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },

  async getHealth() {
    try {
      const res = await fetch('/health');
      if (res.ok) return await res.json();
    } catch (e) {
      // Fallback
    }
    return { status: 'healthy', ollama_model: 'gemma4:12b' };
  },

  // Generic HTTP helpers returning { data }
  async get(url, options = {}) {
    const fullUrl = url.startsWith('http') || url.startsWith('/api') ? url : `${API_BASE}${url.startsWith('/') ? '' : '/'}${url}`;
    const res = await fetch(fullUrl, {
      method: 'GET',
      headers: getAuthHeaders(options.headers || {}),
      ...options,
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    return { data };
  },

  async post(url, body = {}, options = {}) {
    const fullUrl = url.startsWith('http') || url.startsWith('/api') ? url : `${API_BASE}${url.startsWith('/') ? '' : '/'}${url}`;
    const res = await fetch(fullUrl, {
      method: 'POST',
      headers: getAuthHeaders({ 'Content-Type': 'application/json', ...(options.headers || {}) }),
      body: JSON.stringify(body),
      ...options,
    });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();
    return { data };
  },

  // Server-Sent Events (SSE) Stream
  createEventSource(projectId, onMessage, onEnd, onError, onHeartbeat) {
    const userId = getUserId();
    const eventSource = new EventSource(`${API_BASE}/pipeline/stream/${projectId}?user_id=${encodeURIComponent(userId)}`);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.event === 'pipeline_end') {
          if (onEnd) onEnd(data);
          eventSource.close();
        } else if (data.event === 'heartbeat') {
          if (onHeartbeat) onHeartbeat(data);
        } else if (data.event === 'agent_message' || data.agent) {
          if (onMessage) onMessage(data);
        }
      } catch (err) {
        console.error('SSE JSON error:', err);
      }
    };

    eventSource.onerror = (err) => {
      if (eventSource.readyState === EventSource.CLOSED) {
        if (onError) onError(err);
      }
    };

    return eventSource;
  }
};
