import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : '/api';

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

/** Extrai mensagem legível de erros FastAPI/Axios (detail string ou lista de validação). */
export function formatApiError(error, fallback = 'Ocorreu um erro. Tente novamente.') {
  const d = error.response?.data?.detail;
  if (Array.isArray(d)) {
    return d
      .map((item) => (typeof item === 'string' ? item : item?.msg || JSON.stringify(item)))
      .join(' ');
  }
  if (typeof d === 'string' && d.trim()) return d;
  if (error.code === 'ERR_NETWORK' || error.message === 'Network Error') {
    return 'Não foi possível contactar o servidor. Confirme que a API está a correr e VITE_API_URL.';
  }
  if (error.message) return error.message;
  return fallback;
}

// Anexa o JWT de sessão em todas as requisições, se disponível
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('empatia_access_token');
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

/**
 * Verifica se a autenticação Google está disponível no servidor.
 * @returns {Promise<boolean>}
 */
export const checkGoogleAuthStatus = async () => {
  try {
    const response = await apiClient.get('/auth/google/status');
    return response.data?.available === true;
  } catch {
    return false;
  }
};

/**
 * Autentica com Google enviando o ID Token ao backend para verificação server-side.
 * @param {string} credential - ID Token JWT emitido pelo Google Identity Services.
 * @returns {Promise<{access_token: string, user: object}>}
 */
export const loginWithGoogle = async (credential) => {
  try {
    const response = await apiClient.post('/auth/google', { credential });
    const { access_token, user } = response.data;
    localStorage.setItem('empatia_access_token', access_token);
    return { access_token, user };
  } catch (error) {
    console.error('Erro na autenticação Google:', error.response?.data || error.message);
    throw error;
  }
};

/**
 * Envia uma mensagem para o chat e recebe a resposta da IA.
 * @param {string} message - A mensagem do usuário.
 * @param {string} sessionId - O ID da sessão atual.
 * @param {object} sessionObjective - Objetivo da sessão terapêutica (opcional).
 * @param {boolean} isVoiceMode - Indica se está no modo de voz (opcional).
 * @returns {Promise<object>} A resposta da IA.
 */
export const sendMessage = async (message, sessionId, sessionObjective = null, isVoiceMode = false) => {
  try {
    const payload = {
      message,
      session_id: sessionId,
      is_voice_mode: isVoiceMode, // ✅ NOVO: Indicador de modo de voz
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
    
    console.log(`🚀 API - Iniciando envio de mensagem`);
    console.log(`📋 API - SessionId: ${sessionId}`);
    console.log(`💬 API - Mensagem: "${message}"`);
    console.log(`🎤 API - VoiceMode: ${isVoiceMode ? 'ATIVO' : 'INATIVO'}`);
    console.log(`📦 API - Payload completo:`, payload);
    
    const response = await apiClient.post('/chat/send', payload);
    
    console.log(`✅ API - Resposta recebida:`, response.data);
    console.log(`🔍 API - Status: ${response.status}`);
    
    return response.data;
  } catch (error) {
    console.error('❌ API - Erro completo:', error);
    console.error('❌ API - Response data:', error.response?.data);
    console.error('❌ API - Status:', error.response?.status);
    console.error('❌ API - Headers:', error.response?.headers);
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
    const fullName = userData?.full_name || userData?.fullName || userData?.display_name || userData?.name || '';
    const displayName = userData?.display_name || userData?.displayName || fullName || '';

    // Primeiro, criar ou atualizar o usuário no sistema
    if (userData && userData.authMethod === 'google') {
      // Para usuários Google, criar/atualizar no sistema de usuários
      const userPayload = {
        username: username,
        email: userData.email,
        preferences: {
          selected_voice: selectedVoice,
          voice_enabled: voiceEnabled,
          full_name: fullName,
          display_name: displayName,
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

      await apiClient.put(`/user/${username}/preferences`, userPayload.preferences);
      
      // Registrar login
      await apiClient.post(`/user/${username}/login`);
    }

    // Salvar preferências da sessão
    const payload = {
      session_id: sessionId,
      username,
      selected_voice: selectedVoice,
      voice_enabled: voiceEnabled,
      full_name: fullName,
      display_name: displayName,
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

export const getInitialMessage = async (sessionId) => {
  try {
    const response = await fetch(`${API_BASE}/chat/initial-message/${sessionId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Erro ao buscar mensagem inicial:', error);
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
