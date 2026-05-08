import React, { useEffect, useState } from 'react';
import { Loader2 } from 'lucide-react';
import { loginWithGoogle, checkGoogleAuthStatus, formatApiError } from '../services/api.js';

const GoogleAuth = ({ onAuthSuccess, onAuthError }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [serverAvailable, setServerAvailable] = useState(null); // null = verificando

  const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

  useEffect(() => {
    let cancelled = false;

    const initGoogleAuth = async () => {
      // 1. Verificar se VITE_GOOGLE_CLIENT_ID está disponível no frontend
      if (!GOOGLE_CLIENT_ID) {
        if (!cancelled) setError('Login com Google indisponível neste ambiente.');
        if (!cancelled) setServerAvailable(false);
        return;
      }

      // 2. Verificar se o backend está configurado antes de carregar o SDK
      const available = await checkGoogleAuthStatus();
      if (cancelled) return;

      if (!available) {
        setServerAvailable(false);
        setError('Login com Google indisponível neste ambiente.');
        return;
      }

      setServerAvailable(true);

      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);

      script.onload = () => {
        if (!window.google || cancelled) return;

        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleCredentialResponse,
          auto_select: false,
          cancel_on_tap_outside: true,
          context: 'signin',
          ux_mode: 'popup',
        });

        window.google.accounts.id.renderButton(
          document.getElementById('google-signin-button'),
          {
            theme: 'filled_blue',
            size: 'large',
            text: 'signin_with',
            shape: 'pill',
            width: 280,
          }
        );
      };

      return () => {
        cancelled = true;
        if (document.head.contains(script)) {
          document.head.removeChild(script);
        }
      };
    };

    const cleanup = initGoogleAuth();
    return () => {
      cancelled = true;
      cleanup?.then?.((fn) => fn?.());
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [GOOGLE_CLIENT_ID]);

  const handleCredentialResponse = async (response) => {
    if (!response?.credential) {
      const err = new Error('Resposta inválida do Google');
      setError('Erro na resposta do Google. Tente novamente.');
      onAuthError(err);
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      // Verificação server-side: envia o ID Token ao backend
      const { user } = await loginWithGoogle(response.credential);

      onAuthSuccess(user);
    } catch (err) {
      console.error('Erro na autenticação Google:', err.response?.data || err);
      setError(formatApiError(err, 'Erro ao autenticar com Google. Tente novamente.'));
      onAuthError(err);
    } finally {
      setIsLoading(false);
    }
  };

  if (serverAvailable === null) {
    return (
      <div className="flex items-center justify-center gap-2 py-3 text-text-secondary dark:text-text-secondary-dark">
        <Loader2 className="w-4 h-4 animate-spin shrink-0" />
        <span className="text-sm">Verificando autenticação...</span>
      </div>
    );
  }

  if (serverAvailable === false) {
    return (
      <p className="w-full text-amber-700 dark:text-amber-400 text-sm text-center bg-amber-50 dark:bg-amber-900/20 p-3 rounded-lg border border-amber-200 dark:border-amber-700/50">
        Login com Google não está disponível neste momento. Entre em contato com o suporte.
      </p>
    );
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <div id="google-signin-container" className="flex w-full flex-col items-center gap-2">
        <div id="google-signin-button" className="w-full flex justify-center min-h-[44px]" />

        {isLoading && (
          <div className="flex items-center gap-2 text-text-secondary dark:text-text-secondary-dark">
            <Loader2 className="w-4 h-4 animate-spin shrink-0" />
            <span className="text-sm">Autenticando...</span>
          </div>
        )}

        {error && (
          <p className="w-full text-red-600 text-sm text-center bg-red-50 dark:bg-red-950/30 dark:text-red-300 p-2.5 rounded-lg border border-red-100 dark:border-red-900/50">
            {error}
          </p>
        )}
      </div>

      <p className="text-center text-xs text-text-secondary/80 dark:text-text-secondary-dark/80 max-w-[260px] leading-snug">
        Dados protegidos; usamos apenas o necessário para a sua sessão.
      </p>
    </div>
  );
};

export default GoogleAuth;
