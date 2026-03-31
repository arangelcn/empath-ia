import React, { createContext, useContext, useReducer } from 'react';

const AuthContext = createContext();

const authReducer = (state, action) => {
  switch (action.type) {
    case 'LOGIN':
      localStorage.setItem('admin_auth', JSON.stringify({
        isAuthenticated: true,
        user: action.payload
      }));
      return {
        ...state,
        isAuthenticated: true,
        user: action.payload
      };
    case 'LOGOUT':
      localStorage.removeItem('admin_auth');
      return {
        ...state,
        isAuthenticated: false,
        user: null
      };
    case 'INIT':
      const savedAuth = localStorage.getItem('admin_auth');
      if (savedAuth) {
        const authData = JSON.parse(savedAuth);
        return {
          ...state,
          isAuthenticated: authData.isAuthenticated,
          user: authData.user
        };
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
    // Simulação de autenticação - em produção, isso seria uma chamada à API
    if (credentials.username === 'admin' && credentials.password === 'admin123') {
      const user = {
        id: 1,
        username: 'admin',
        name: 'Administrador',
        email: 'admin@empat-ia.io',
        role: 'admin'
      };
      dispatch({ type: 'LOGIN', payload: user });
      return { success: true };
    } else {
      return { success: false, error: 'Credenciais inválidas' };
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