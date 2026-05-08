import React, { createContext, useContext, useReducer } from 'react';
import apiService from '../services/api';

const AuthContext = createContext();

const authReducer = (state, action) => {
  switch (action.type) {
    case 'LOGIN':
      localStorage.setItem('admin_auth', JSON.stringify({
        isAuthenticated: true,
        user: action.payload.user
      }));
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload.user
      };
    case 'LOGOUT':
      localStorage.removeItem('admin_auth');
      apiService.clearToken();
      return {
        ...state,
        isAuthenticated: false,
        user: null
      };
    case 'INIT':
      const savedAuth = localStorage.getItem('admin_auth');
      if (savedAuth) {
        try {
          const authData = JSON.parse(savedAuth);
          return {
            ...state,
            isAuthenticated: Boolean(authData.isAuthenticated && apiService.getToken()),
            user: authData.user
          };
        } catch {
          localStorage.removeItem('admin_auth');
        }
      }
      return state;
    default:
      return state;
  }
};

const initialState = {
  isAuthenticated: false,
  user: null
};

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(authReducer, initialState);

  React.useEffect(() => {
    dispatch({ type: 'INIT' });
  }, []);

  const login = async (credentials) => {
    try {
      const session = await apiService.loginAdmin(credentials);
      dispatch({ type: 'LOGIN', payload: session });
      return { success: true };
    } catch (error) {
      return { success: false, error: apiService.formatError(error, 'Credenciais inválidas') };
    }
  };

  const logout = () => {
    dispatch({ type: 'LOGOUT' });
  };

  const value = {
    ...state,
    login,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth deve ser usado dentro de um AuthProvider');
  }
  return context;
} 
