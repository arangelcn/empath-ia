import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api', // O gateway irá redirecionar
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Envia uma mensagem para o chat e recebe a resposta da IA.
 * @param {string} message - A mensagem do usuário.
 * @param {string} sessionId - O ID da sessão atual.
 * @param {object} sessionObjective - Objetivo da sessão terapêutica (opcional).
 * @returns {Promise<object>} A resposta da IA.
 */
export const sendMessage = async (message, sessionId, sessionObjective = null) => {
  try {
    const payload = {
      message,
      session_id: sessionId,
    };
    
    // Adicionar objetivo da sessão se fornecido
    if (sessionObjective) {
      payload.session_objective = {
        title: sessionObjective.title,
        subtitle: sessionObjective.subtitle,
        objective: sessionObjective.objective,
        initial_prompt: sessionObjective.initial_prompt
      };
    }
    
    const response = await apiClient.post('/chat/send', payload);
    return response.data;
  } catch (error) {
    console.error('Erro ao enviar mensagem:', error.response?.data || error.message);
    throw error;
  }
};

/**
 * Busca o status de onboarding do usuário.
 * @param {string} sessionId - O ID da sessão atual.
 * @returns {Promise<object>} O status do usuário.
 */
export const getUserStatus = async (sessionId) => {
  try {
    const response = await apiClient.get(`/user/status/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar status do usuário:', error.response?.data || error.message);
    throw error;
  }
};

/**
 * Salva as preferências do usuário.
 * @param {string} sessionId - O ID da sessão atual.
 * @param {string} username - O nome do usuário.
 * @param {string} selectedVoice - A voz selecionada.
 * @param {boolean} voiceEnabled - Se o serviço de voz está habilitado.
 * @param {object} userData - Dados do usuário autenticado (opcional).
 * @returns {Promise<object>} A confirmação do salvamento.
 */
export const saveUserPreferences = async (sessionId, username, selectedVoice, voiceEnabled = true, userData = null) => {
  try {
    // Primeiro, criar ou atualizar o usuário no sistema
    if (userData && userData.authMethod === 'google') {
      // Para usuários Google, criar/atualizar no sistema de usuários
      const userPayload = {
        username: username,
        email: userData.email,
        preferences: {
          selected_voice: selectedVoice,
          voice_enabled: voiceEnabled,
          theme: 'dark',
          language: 'pt-BR'
        }
      };
      
      try {
        await apiClient.post('/user/create', userPayload);
      } catch (error) {
        if (error.response?.status !== 400) { // 400 = usuário já existe
          console.warn('Erro ao criar usuário:', error);
        }
      }
      
      // Registrar login
      await apiClient.post(`/user/${username}/login`);
    }

    // Salvar preferências da sessão
    const payload = {
      session_id: sessionId,
      username,
      selected_voice: selectedVoice,
      voice_enabled: voiceEnabled,
    };

    // Adicionar dados do usuário se disponíveis
    if (userData) {
      payload.user_data = userData;
    }

    const response = await apiClient.post('/user/preferences', payload);
    return response.data;
  } catch (error) {
    console.error('Erro ao salvar preferências:', error.response?.data || error.message);
    throw error;
  }
};

/**
 * Busca o histórico de mensagens de uma sessão.
 * @param {string} sessionId - O ID da sessão atual.
 * @returns {Promise<object>} O histórico de mensagens.
 */
export const getChatHistory = async (sessionId) => {
  try {
    const response = await apiClient.get(`/chat/history/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar histórico de mensagens:', error.response?.data || error.message);
    throw error;
  }
};

/**
 * Criar novo usuário.
 * @param {string} username - Nome do usuário.
 * @param {string} email - Email do usuário (opcional).
 * @param {object} preferences - Preferências do usuário (opcional).
 * @returns {Promise<object>} Dados do usuário criado.
 */
export const createUser = async (username, email = null, preferences = null) => {
  try {
    const payload = { username };
    if (email) payload.email = email;
    if (preferences) payload.preferences = preferences;
    
    const response = await apiClient.post('/user/create', payload);
    return response.data;
  } catch (error) {
    console.error('Erro ao criar usuário:', error.response?.data || error.message);
    throw error;
  }
};

/**
 * Obter dados de um usuário.
 * @param {string} username - Nome do usuário.
 * @returns {Promise<object>} Dados do usuário.
 */
export const getUser = async (username) => {
  try {
    const response = await apiClient.get(`/user/${username}`);
    return response.data;
  } catch (error) {
    console.error('Erro ao obter usuário:', error.response?.data || error.message);
    throw error;
  }
};

/**
 * Atualizar preferências do usuário.
 * @param {string} username - Nome do usuário.
 * @param {object} preferences - Novas preferências.
 * @returns {Promise<object>} Confirmação da atualização.
 */
export const updateUserPreferences = async (username, preferences) => {
  try {
    const response = await apiClient.put(`/user/${username}/preferences`, preferences);
    return response.data;
  } catch (error) {
    console.error('Erro ao atualizar preferências:', error.response?.data || error.message);
    throw error;
  }
};

/**
 * Registrar login do usuário.
 * @param {string} username - Nome do usuário.
 * @returns {Promise<object>} Confirmação do login.
 */
export const userLogin = async (username) => {
  try {
    const response = await apiClient.post(`/user/${username}/login`);
    return response.data;
  } catch (error) {
    console.error('Erro ao registrar login:', error.response?.data || error.message);
    throw error;
  }
};

/**
 * Obter estatísticas do usuário.
 * @param {string} username - Nome do usuário.
 * @returns {Promise<object>} Estatísticas do usuário.
 */
export const getUserStats = async (username) => {
  try {
    const response = await apiClient.get(`/user/${username}/stats`);
    return response.data;
  } catch (error) {
    console.error('Erro ao obter estatísticas:', error.response?.data || error.message);
    throw error;
  }
};

/**
 * Buscar sessões terapêuticas ativas.
 * @param {number} limit - Quantidade máxima de sessões (opcional).
 * @returns {Promise<object>} Lista de sessões ativas.
 */
export const getActiveTherapeuticSessions = async (limit = 50) => {
  try {
    const response = await apiClient.get(`/sessions?active_only=true&limit=${limit}`);
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar sessões terapêuticas ativas:', error.response?.data || error.message);
    throw error;
  }
};

/**
 * Obter detalhes de uma sessão terapêutica específica.
 * @param {string} sessionId - ID da sessão.
 * @returns {Promise<object>} Detalhes da sessão.
 */
export const getTherapeuticSession = async (sessionId) => {
  try {
    const response = await apiClient.get(`/sessions/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar sessão terapêutica:', error.response?.data || error.message);
    throw error;
  }
};

/**
 * Marcar uma sessão como concluída.
 * @param {string} sessionId - ID da sessão.
 * @param {string} userId - ID do usuário.
 * @returns {Promise<object>} Confirmação da conclusão.
 */
export const completeSession = async (sessionId, userId) => {
  try {
    const response = await apiClient.post('/session/complete', {
      session_id: sessionId,
      user_id: userId
    });
    return response.data;
  } catch (error) {
    console.error('Erro ao marcar sessão como concluída:', error.response?.data || error.message);
    throw error;
  }
};

// ===== APIs DE SESSÕES TERAPÊUTICAS DOS USUÁRIOS =====

export const getUserSessions = async (username, status = null) => {
  try {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    
    const url = `/user/${username}/sessions?${params}`;
    const response = await apiClient.get(url);
    
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar sessões do usuário:', error.response?.data || error.message);
    throw error;
  }
};

export const getUserSession = async (username, sessionId) => {
  try {
    const response = await apiClient.get(`/user/${username}/sessions/${sessionId}`);
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar sessão do usuário:', error.response?.data || error.message);
    throw error;
  }
};

export const unlockUserSession = async (username, sessionId) => {
  try {
    const response = await apiClient.post(`/user/${username}/sessions/${sessionId}/unlock`);
    return response.data;
  } catch (error) {
    console.error('Erro ao desbloquear sessão:', error.response?.data || error.message);
    throw error;
  }
};

export const startUserSession = async (username, sessionId) => {
  try {
    const response = await apiClient.post(`/user/${username}/sessions/${sessionId}/start`);
    return response.data;
  } catch (error) {
    console.error('Erro ao iniciar sessão:', error.response?.data || error.message);
    throw error;
  }
};

export const completeUserSession = async (username, sessionId, progress = 100) => {
  try {
    const response = await apiClient.post(`/user/${username}/sessions/${sessionId}/complete`, { progress });
    return response.data;
  } catch (error) {
    console.error('Erro ao concluir sessão:', error.response?.data || error.message);
    throw error;
  }
};

export const getUserProgress = async (username) => {
  try {
    const response = await apiClient.get(`/user/${username}/progress`);
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar progresso do usuário:', error.response?.data || error.message);
    throw error;
  }
};

// ===== APIs DE USUÁRIO ===== 

export const getSessions = async () => {
  try {
    const response = await apiClient.get('/sessions');
    return response.data;
  } catch (error) {
    console.error('Erro ao buscar sessões:', error.response?.data || error.message);
    throw error;
  }
}; 