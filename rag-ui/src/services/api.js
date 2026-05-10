
const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Token helpers
function getAccessToken() {
  return localStorage.getItem('access_token');
}
function getRefreshToken() {
  return localStorage.getItem('refresh_token');
}
function setTokens({ access_token, refresh_token }) {
  if (access_token) localStorage.setItem('access_token', access_token);
  if (refresh_token) localStorage.setItem('refresh_token', refresh_token);
}
function clearTokens() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
}

async function fetchWithAuth(url, options = {}, tryRefresh = true) {
  let token = getAccessToken();
  options.headers = options.headers || {};
  if (token) options.headers['Authorization'] = `Bearer ${token}`;
  let res = await fetch(url, options);
  if (res.status === 401 && tryRefresh && getRefreshToken()) {
    // Try to refresh token
    const ok = await api.refreshToken();
    if (ok) {
      token = getAccessToken();
      options.headers['Authorization'] = `Bearer ${token}`;
      res = await fetch(url, options);
    } else {
      clearTokens();
    }
  }
  return res;
}

export const api = {

  // --- AUTH ---
  
  // POST /auth/register - CreateUserRequest
  async register(userData) {
    // userData: { username, email, password, role, first_name, last_name }
    const res = await fetch(`${BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Registration failed');
    }
    return res.json();
  },

  // GET /auth/me
  async getMe() {
    const res = await fetchWithAuth(`${BASE_URL}/auth/me`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch user details');
    }
    return res.json();
  },

  // POST /auth/login - form data (application/x-www-form-urlencoded)
  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    formData.append('grant_type', 'password');
    
    const res = await fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Login failed');
    }
    const tokens = await res.json();
    setTokens(tokens);
    return tokens;
  },

  // POST /auth/refresh - RefreshTokenRequest
  async refreshToken() {
    const refresh_token = getRefreshToken();
    if (!refresh_token) return false;
    const res = await fetch(`${BASE_URL}/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token })
    });
    if (!res.ok) {
      clearTokens();
      return false;
    }
    const tokens = await res.json();
    setTokens(tokens);
    return true;
  },

  // POST /auth/logout
  async logout() {
    try {
      await fetchWithAuth(`${BASE_URL}/auth/logout`, { method: 'POST' });
    } catch {}
    clearTokens();
  },

  // POST /auth/forgot-password
  async forgotPassword(email) {
    const res = await fetch(`${BASE_URL}/auth/forgot-password`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Forgot password request failed');
    }
    return res.json();
  },

  // --- END AUTH ---

  async checkHealth() {
    const res = await fetchWithAuth(`${BASE_URL}/rag/health`);
    if (!res.ok) throw new Error('Server unreachable');
    return res.json();
  },


  async uploadPdf(file, onProgress) {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const form = new FormData();
      form.append('file', file);
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      });

      xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          resolve(JSON.parse(xhr.responseText));
        } else {
          try {
            const err = JSON.parse(xhr.responseText);
            reject(new Error(err.detail || 'Upload failed'));
          } catch { reject(new Error('Upload failed')); }
        }
      });

      xhr.addEventListener('error', () => reject(new Error('Network error')));
      xhr.open('POST', `${BASE_URL}/ingest/pdf`);
      const token = getAccessToken();
      if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
      xhr.send(form);
    });
  },

  // ✅ evaluate param added
  async askQuestion(question, evaluate = true, model = null, modelParams = null) {
    const payload = { 
      question, 
      evaluate, 
      ...(model && { model_name: model }),
      ...(modelParams && Object.keys(modelParams).length > 0 && { model_params: modelParams })
    };
    console.log('📤 Sending to /rag/ask:', payload);
    const res = await fetchWithAuth(`${BASE_URL}/rag/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to get answer');
    }
    return res.json();
  },

  // ✅ NEW: Stream RAG answer
  async *askQuestionStream(question, evaluate = true, model = null, modelParams = null) {
    const payload = { 
      question, 
      evaluate, 
      ...(model && { model_name: model }),
      ...(modelParams && Object.keys(modelParams).length > 0 && { model_params: modelParams })
    };
    console.log('📤 Streaming to /rag/ask-stream:', payload);
    
    const token = getAccessToken();
    const headers = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const res = await fetch(`${BASE_URL}/rag/ask-stream`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to stream answer');
    }

    // Handle Server-Sent Events stream
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Keep incomplete line in buffer

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              yield data;
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  },

  // ✅ Get available LLM models
  async getModels() {
    const res = await fetchWithAuth(`${BASE_URL}/rag/models`);
    if (!res.ok) throw new Error('Failed to fetch models');
    return res.json();
  },

  async getDocuments() {
    const res = await fetchWithAuth(`${BASE_URL}/ingest/documents`);
    if (!res.ok) throw new Error('Failed to fetch documents');
    return res.json();
  },

  async cleanupExpiredTokens() {
    const res = await fetchWithAuth(`${BASE_URL}/auth/cleanup-expired-tokens`, { method: 'POST' });
    if (!res.ok) throw new Error('Failed to cleanup expired tokens');
    return res.json();
  },

  async resetVectorStore() {
    const res = await fetchWithAuth(`${BASE_URL}/ingest/vector-store`, { method: 'DELETE' });
    if (!res.ok) throw new Error('Failed to reset vector store');
    return res.json();
  },
};