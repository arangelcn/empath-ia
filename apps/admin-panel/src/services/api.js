/**
 * Serviço de API para comunicação com o backend
 */

// No Docker, o browser acessa via localhost:8000 (porta mapeada do gateway)
const API_BASE_URL = 'http://localhost:8000';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
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

  // Dashboard Stats
  async getDashboardStats() {
    return this.get('/api/admin/stats');
  }

  // Conversations
  async getConversations(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const endpoint = `/api/admin/conversations${queryString ? `?${queryString}` : ''}`;
    return this.get(endpoint);
  }

  async getConversationDetails(sessionId) {
    return this.get(`/api/admin/conversations/${sessionId}`);
  }

  // ===== NOVOS ENDPOINTS PARA USUÁRIOS =====

  // Usuários
  async getUsers(params = {}) {
    const queryString = new URLSearchParams(params).toString();
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
    const queryString = new URLSearchParams(params).toString();
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
    const queryString = new URLSearchParams(params).toString();
    const endpoint = `/api/user/${username}/sessions${queryString ? `?${queryString}` : ''}`;
    return this.get(endpoint);
  }

  async getUserSessionDetails(username, sessionId) {
    return this.get(`/api/user/${username}/sessions/${sessionId}`);
  }

  async getAllUserSessions(params = {}) {
    // Buscar todas as sessões de todos os usuários via admin
    const queryString = new URLSearchParams(params).toString();
    const endpoint = `/api/admin/user-sessions${queryString ? `?${queryString}` : ''}`;
    return this.get(endpoint);
  }

  // ===== NOVOS ENDPOINTS PARA CONTEXTOS E RESUMOS =====

  // Contextos de Sessão
  async getSessionContext(sessionId) {
    return this.get(`/api/admin/session-contexts/${sessionId}`);
  }

  async getAllSessionContexts(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const endpoint = `/api/admin/session-contexts${queryString ? `?${queryString}` : ''}`;
    return this.get(endpoint);
  }

  // Novo endpoint otimizado para buscar todas as sessões dos usuários com contextos
  async getAllUserSessionsWithContexts(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const endpoint = `/api/admin/user-sessions${queryString ? `?${queryString}` : ''}`;
    return this.get(endpoint);
  }

  // Emotions Analysis
  async getEmotionsAnalysis(days = 7) {
    return this.get(`/api/admin/emotions/analysis?days=${days}`);
  }

  async getUserEmotions(username, params = {}) {
    const queryString = new URLSearchParams(params).toString();
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
    const queryString = new URLSearchParams(params).toString();
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