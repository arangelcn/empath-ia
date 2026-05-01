/**
 * Serviço de API para comunicação com o backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const ADMIN_TOKEN_KEY = 'admin_access_token';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  getToken() {
    return localStorage.getItem(ADMIN_TOKEN_KEY);
  }

  setToken(token) {
    if (token) {
      localStorage.setItem(ADMIN_TOKEN_KEY, token);
    }
  }

  clearToken() {
    localStorage.removeItem(ADMIN_TOKEN_KEY);
  }

  buildQuery(params = {}) {
    const cleanParams = Object.entries(params).reduce((acc, [key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        acc[key] = value;
      }
      return acc;
    }, {});
    return new URLSearchParams(cleanParams).toString();
  }

  formatError(error, fallback = 'Erro ao comunicar com o backend.') {
    if (error?.detail) {
      if (Array.isArray(error.detail)) {
        return error.detail.map((item) => item.msg || String(item)).join(' ');
      }
      return error.detail;
    }
    if (error?.message) return error.message;
    return fallback;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = this.getToken();
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      const text = await response.text();
      let data = null;
      if (text) {
        try {
          data = JSON.parse(text);
        } catch {
          data = { message: text };
        }
      }
      
      if (!response.ok) {
        const message = this.formatError(data, `HTTP ${response.status}`);
        const error = new Error(message);
        error.status = response.status;
        error.payload = data;
        throw error;
      }
      
      return data;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  // Métodos GET
  async get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  // Métodos POST
  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Métodos PUT
  async put(endpoint, data) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  // Métodos DELETE
  async delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  // ===== ENDPOINTS ESPECÍFICOS DO ADMIN =====

  async loginAdmin(credentials) {
    const response = await this.post('/api/auth/admin/login', credentials);
    this.setToken(response.access_token);
    return response;
  }

  // Dashboard Stats
  async getDashboardStats() {
    return this.get('/api/admin/stats');
  }

  async getAnalytics(days = 7) {
    return this.get(`/api/admin/analytics?days=${days}`);
  }

  async getSystemStatus() {
    return this.get('/api/admin/system-status');
  }

  // Conversations
  async getConversations(params = {}) {
    const queryString = this.buildQuery(params);
    const endpoint = `/api/admin/conversations${queryString ? `?${queryString}` : ''}`;
    return this.get(endpoint);
  }

  async getConversationDetails(sessionId) {
    return this.get(`/api/admin/conversations/${sessionId}`);
  }

  // ===== NOVOS ENDPOINTS PARA USUÁRIOS =====

  // Usuários
  async getUsers(params = {}) {
    const queryString = this.buildQuery(params);
    const endpoint = `/api/admin/users${queryString ? `?${queryString}` : ''}`;
    return this.get(endpoint);
  }

  async getUserDetails(username) {
    return this.get(`/api/admin/users/${username}`);
  }

  async getUserStats(username) {
    return this.get(`/api/admin/users/${username}/stats`);
  }

  async createUser(userData) {
    return this.post('/api/admin/users', userData);
  }

  async updateUser(username, userData) {
    return this.put(`/api/admin/users/${username}`, userData);
  }

  async deleteUser(username) {
    return this.delete(`/api/admin/users/${username}`);
  }

  // ===== NOVOS ENDPOINTS PARA SESSÕES TERAPÊUTICAS =====

  // Sessões Terapêuticas (Templates)
  async getTherapeuticSessions(params = {}) {
    const queryString = this.buildQuery(params);
    const endpoint = `/api/admin/therapeutic-sessions${queryString ? `?${queryString}` : ''}`;
    return this.get(endpoint);
  }

  async createTherapeuticSession(sessionData) {
    return this.post('/api/admin/therapeutic-sessions', sessionData);
  }

  async updateTherapeuticSession(sessionId, sessionData) {
    return this.put(`/api/admin/therapeutic-sessions/${sessionId}`, sessionData);
  }

  async deleteTherapeuticSession(sessionId) {
    return this.delete(`/api/admin/therapeutic-sessions/${sessionId}`);
  }

  // Sessões dos Usuários
  async getUserSessions(username, params = {}) {
    const queryString = this.buildQuery(params);
    const endpoint = `/api/user/${username}/sessions${queryString ? `?${queryString}` : ''}`;
    return this.get(endpoint);
  }

  async getUserSessionDetails(username, sessionId) {
    return this.get(`/api/user/${username}/sessions/${sessionId}`);
  }

  async getAllUserSessions(params = {}) {
    // Buscar todas as sessões de todos os usuários via admin
    const queryString = this.buildQuery(params);
    const endpoint = `/api/admin/user-sessions${queryString ? `?${queryString}` : ''}`;
    return this.get(endpoint);
  }

  // ===== NOVOS ENDPOINTS PARA CONTEXTOS E RESUMOS =====

  // Contextos de Sessão
  async getSessionContext(sessionId) {
    return this.get(`/api/admin/session-contexts/${sessionId}`);
  }

  async getAllSessionContexts(params = {}) {
    const queryString = this.buildQuery(params);
    const endpoint = `/api/admin/session-contexts${queryString ? `?${queryString}` : ''}`;
    return this.get(endpoint);
  }

  // Novo endpoint otimizado para buscar todas as sessões dos usuários com contextos
  async getAllUserSessionsWithContexts(params = {}) {
    const queryString = this.buildQuery(params);
    const endpoint = `/api/admin/user-sessions${queryString ? `?${queryString}` : ''}`;
    return this.get(endpoint);
  }

  // Emotions Analysis
  async getEmotionsAnalysis(days = 7) {
    return this.get(`/api/admin/emotions/analysis?days=${days}`);
  }

  async getUserEmotions(username, params = {}) {
    const queryString = this.buildQuery(params);
    const endpoint = `/api/emotions/${username}${queryString ? `?${queryString}` : ''}`;
    return this.get(endpoint);
  }

  // Real-time Activity
  async getRealTimeActivity() {
    return this.get('/api/admin/activity/realtime');
  }

  // Chat API (original)
  async getChatHistory(sessionId) {
    return this.get(`/api/chat/history/${sessionId}`);
  }

  async listChatConversations() {
    return this.get('/api/chat/conversations');
  }

  // ===== NOVOS ENDPOINTS PARA PROMPTS =====

  // Prompts
  async getPrompts(params = {}) {
    const queryString = this.buildQuery(params);
    const endpoint = `/api/prompts${queryString ? `?${queryString}` : ''}`;
    return this.get(endpoint);
  }

  async getPrompt(promptKey) {
    return this.get(`/api/prompts/${promptKey}`);
  }

  async createPrompt(promptData) {
    return this.post('/api/prompts', promptData);
  }

  async updatePrompt(promptKey, promptData) {
    return this.put(`/api/prompts/${promptKey}`, promptData);
  }

  async deletePrompt(promptKey) {
    return this.delete(`/api/prompts/${promptKey}`);
  }

  async getPromptsStats() {
    return this.get('/api/prompts/stats');
  }

  async initializeDefaultPrompts() {
    return this.post('/api/prompts/initialize');
  }

  async renderPrompt(promptKey, variables) {
    return this.post(`/api/prompts/${promptKey}/render`, { variables });
  }
}

export default new ApiService(); 
