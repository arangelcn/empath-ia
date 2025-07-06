import React, { useEffect, useState } from 'react';
import { Chrome, Loader2 } from 'lucide-react';

const GoogleAuth = ({ onAuthSuccess, onAuthError }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Google OAuth 2.0 configuration
  const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || 'your-google-client-id';
  const GOOGLE_REDIRECT_URI = import.meta.env.VITE_GOOGLE_REDIRECT_URI || window.location.origin;

  useEffect(() => {
    // Load Google OAuth script
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);

    script.onload = () => {
      if (window.google) {
        // Initialize Google Identity Services
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleCredentialResponse,
          auto_select: false,
          cancel_on_tap_outside: true,
          // Configurações avançadas
          context: 'signin',
          ux_mode: 'popup',
          prompt_parent_id: 'google-signin-container',
          // One Tap (opcional - pode ser habilitado depois)
          // one_tap: true,
          // auto_select: true,
        });

        // Render the sign-in button
        window.google.accounts.id.renderButton(
          document.getElementById('google-signin-button'),
          {
            theme: 'filled_blue',
            size: 'large',
            text: 'signin_with',
            shape: 'pill',
            width: 350,
            height: 50,
            // Configurações avançadas do botão
            click_listener: () => {
              console.log('Google Sign-In button clicked');
            },
          }
        );

        // Opcional: Habilitar One Tap (descomente se quiser)
        // window.google.accounts.id.prompt((notification) => {
        //   if (notification.isNotDisplayed() || notification.isSkippedMoment()) {
        //     console.log('One Tap not displayed or skipped');
        //   }
        // });
      }
    };

    return () => {
      // Cleanup
      if (document.head.contains(script)) {
        document.head.removeChild(script);
      }
    };
  }, []);

  const handleCredentialResponse = async (response) => {
    setIsLoading(true);
    setError('');

    try {
      // Validate response
      if (!response || !response.credential) {
        throw new Error('Resposta inválida do Google');
      }

      // Decode the JWT token to get user info
      const payload = JSON.parse(atob(response.credential.split('.')[1]));
      
      // Validate required fields
      if (!payload.sub || !payload.email || !payload.name) {
        throw new Error('Informações do usuário incompletas');
      }

      const userData = {
        id: payload.sub,
        email: payload.email,
        name: payload.name,
        picture: payload.picture || null,
        given_name: payload.given_name || '',
        family_name: payload.family_name || '',
        email_verified: payload.email_verified || false,
        locale: payload.locale || 'pt-BR',
        // Timestamp de quando o token foi emitido
        issued_at: payload.iat ? new Date(payload.iat * 1000) : new Date(),
      };

      // Validate email verification (opcional)
      if (!userData.email_verified) {
        console.warn('Email não verificado pelo Google');
      }

      // Store user data in localStorage
      localStorage.setItem('empatia_user', JSON.stringify(userData));
      
      // Call success callback with user data
      onAuthSuccess(userData);
      
    } catch (error) {
      console.error('Erro na autenticação Google:', error);
      
      // Tratamento de erros específicos
      let errorMessage = 'Erro ao autenticar com Google. Tente novamente.';
      
      if (error.message.includes('Resposta inválida')) {
        errorMessage = 'Erro na resposta do Google. Tente novamente.';
      } else if (error.message.includes('Informações incompletas')) {
        errorMessage = 'Informações do usuário incompletas. Tente novamente.';
      } else if (error.message.includes('Network')) {
        errorMessage = 'Erro de conexão. Verifique sua internet.';
      }
      
      setError(errorMessage);
      onAuthError(error);
    } finally {
      setIsLoading(false);
    }
  };

  // Função para limpar dados do usuário (logout)
  const clearUserData = () => {
    localStorage.removeItem('empatia_user');
    // Opcional: Revogar token do Google
    if (window.google && window.google.accounts) {
      window.google.accounts.id.disableAutoSelect();
    }
  };

  return (
    <div className="space-y-6">
      {/* Google Sign-In Button Container */}
      <div id="google-signin-container" className="flex flex-col items-center space-y-4">
        <div id="google-signin-button" className="w-full max-w-sm"></div>
        
        {isLoading && (
          <div className="flex items-center space-x-2 text-gray-600">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">Autenticando...</span>
          </div>
        )}
        
        {error && (
          <p className="text-red-600 text-sm text-center bg-red-50 p-3 rounded-xl">
            {error}
          </p>
        )}
      </div>
      
      <div className="text-center space-y-2">
        <p className="text-sm text-gray-600">
          Faça login com Google para continuar
        </p>
        <p className="text-xs text-gray-500">
          Suas informações são mantidas privadas e seguras
        </p>
        <p className="text-xs text-gray-400">
          Usando Google Identity Services (API mais recente)
        </p>
      </div>
    </div>
  );
};

export default GoogleAuth; 