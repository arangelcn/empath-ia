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

  // Emotions Analysis
  async getEmotionsAnalysis(days = 7) {
    return this.get(`/api/admin/emotions/analysis?days=${days}`);
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

  // System Health
  async getSystemHealth() {
    return this.get('/health');
  }

  async getAllServicesHealth() {
    return this.get('/health/all');
  }

  // ===== ENDPOINTS PARA SESSÕES TERAPÊUTICAS =====

  // Listar sessões terapêuticas
  async getTherapeuticSessions(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const endpoint = `/api/admin/therapeutic-sessions${queryString ? `?${queryString}` : ''}`;
    return this.get(endpoint);
  }

  // Obter detalhes de uma sessão terapêutica
  async getTherapeuticSession(sessionId) {
    return this.get(`/api/admin/therapeutic-sessions/${sessionId}`);
  }

  // Criar nova sessão terapêutica
  async createTherapeuticSession(sessionData) {
    return this.post('/api/admin/therapeutic-sessions', sessionData);
  }

  // Atualizar sessão terapêutica
  async updateTherapeuticSession(sessionId, sessionData) {
    return this.put(`/api/admin/therapeutic-sessions/${sessionId}`, sessionData);
  }

  // Deletar sessão terapêutica
  async deleteTherapeuticSession(sessionId) {
    return this.delete(`/api/admin/therapeutic-sessions/${sessionId}`);
  }
}

// Instância singleton
const apiService = new ApiService();

export default apiService; 