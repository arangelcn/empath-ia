import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api', // O gateway irá redirecionar
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Envia uma mensagem para o chat.
 * @param {string} message - A mensagem do usuário.
 * @param {string} sessionId - O ID da sessão atual.
 * @returns {Promise<object>} A resposta da IA.
 */
export const sendMessage = async (message, sessionId) => {
  try {
    const response = await apiClient.post('/chat/send', {
      message,
      session_id: sessionId,
    });
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
 * @returns {Promise<object>} A confirmação do salvamento.
 */
export const saveUserPreferences = async (sessionId, username, selectedVoice) => {
  try {
    const response = await apiClient.post('/user/preferences', {
      session_id: sessionId,
      username,
      selected_voice: selectedVoice,
    });
    return response.data;
  } catch (error)
  {
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