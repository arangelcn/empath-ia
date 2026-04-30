import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  CheckCircle2,
  Circle,
  Clock,
  Home,
  Lock,
  LogOut,
  Menu,
  MessageCircle,
  RefreshCw,
  Settings,
  Sparkles,
  X,
} from 'lucide-react';
import { getUserProgress, getUserSessions, startUserSession } from '../../services/api.js';

const statusConfig = {
  completed: {
    label: 'Concluida',
    icon: CheckCircle2,
    className: 'text-emerald-600 bg-emerald-50 border-emerald-100',
  },
  in_progress: {
    label: 'Em andamento',
    icon: Clock,
    className: 'text-amber-600 bg-amber-50 border-amber-100',
  },
  unlocked: {
    label: 'Disponivel',
    icon: Circle,
    className: 'text-blue-600 bg-blue-50 border-blue-100',
  },
  locked: {
    label: 'Bloqueada',
    icon: Lock,
    className: 'text-gray-400 bg-gray-50 border-gray-100',
  },
};

const getSessionRank = (session) => {
  const ranks = {
    in_progress: 0,
    unlocked: 1,
    completed: 2,
    locked: 3,
  };
  return ranks[session?.status] ?? 4;
};

const SidebarSession = ({ session, onOpen, disabled }) => {
  const config = statusConfig[session.status] || statusConfig.locked;
  const Icon = config.icon;

  return (
    <button
      type="button"
      onClick={() => onOpen(session)}
      disabled={disabled || session.status === 'locked'}
      className="group flex w-full min-h-0 items-start gap-3 rounded-lg border border-transparent px-3 py-2.5 text-left transition-colors hover:border-gray-200 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
    >
      <span className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full border ${config.className}`}>
        <Icon className="h-3.5 w-3.5" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium text-gray-800">
          {session.title || session.session_id}
        </span>
        <span className="mt-0.5 block truncate text-xs text-gray-500">
          {config.label}
        </span>
      </span>
    </button>
  );
};

const SidebarContent = ({
  username,
  userSessions,
  loadingJourney,
  startingSession,
  onClose,
  onLogout,
  onOpenSession,
  onRefresh,
}) => {
  const navigate = useNavigate();
  const primarySession = userSessions.find(session => session.status === 'in_progress')
    || userSessions.find(session => session.status === 'unlocked');

  const visibleSessions = useMemo(() => (
    [...userSessions]
      .sort((a, b) => getSessionRank(a) - getSessionRank(b) || String(a.title || '').localeCompare(String(b.title || '')))
      .slice(0, 7)
  ), [userSessions]);

  const navLinkClass = ({ isActive }) => [
    'flex min-h-[42px] items-center gap-3 rounded-lg px-3 text-sm font-medium transition-colors',
    isActive ? 'bg-primary-50 text-primary-700' : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900',
  ].join(' ');

  return (
    <aside className="flex h-full w-72 flex-col border-r border-gray-200 bg-white">
      <div className="flex h-16 items-center justify-between border-b border-gray-100 px-4">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-600 text-white">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <p className="font-heading text-base font-semibold text-gray-900">Empat.IA</p>
            <p className="max-w-[170px] truncate text-xs text-gray-500">{username}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          className="flex h-10 w-10 items-center justify-center rounded-lg text-gray-500 hover:bg-gray-100 lg:hidden"
          title="Fechar menu"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-4">
        <button
          type="button"
          onClick={() => {
            if (primarySession) {
              onOpenSession(primarySession);
              return;
            }

            navigate('/home');
            onClose();
          }}
          className="mb-4 flex w-full min-h-[44px] items-center justify-center gap-2 rounded-lg bg-primary-600 px-4 text-sm font-semibold text-white shadow-sm hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={loadingJourney || startingSession === primarySession?.session_id}
        >
          {primarySession ? (
            <>
              <MessageCircle className="h-4 w-4" />
              {primarySession.status === 'in_progress' ? 'Continuar conversa' : 'Iniciar proxima sessao'}
            </>
          ) : (
            <>
              <Home className="h-4 w-4" />
              Ver Home
            </>
          )}
        </button>

        <div className="space-y-1">
          <NavLink to="/home" onClick={onClose} className={navLinkClass}>
            <Home className="h-4 w-4" />
            Home
          </NavLink>
        </div>

        <div className="my-5 border-t border-gray-100" />

        <div>
          <div className="mb-2 flex items-center justify-between px-1">
            <h2 className="text-xs font-semibold uppercase text-gray-500">Sessoes</h2>
            <button
              type="button"
              onClick={onRefresh}
              className="flex h-8 w-8 items-center justify-center rounded-lg text-gray-400 hover:bg-gray-100 hover:text-primary-600"
              title="Atualizar sessoes"
            >
              <RefreshCw className={`h-4 w-4 ${loadingJourney ? 'animate-spin' : ''}`} />
            </button>
          </div>

          <div className="space-y-1">
            {visibleSessions.map(session => (
              <SidebarSession
                key={session.session_id}
                session={session}
                onOpen={onOpenSession}
                disabled={startingSession === session.session_id}
              />
            ))}

            {!loadingJourney && visibleSessions.length === 0 && (
              <p className="px-3 py-4 text-sm text-gray-500">
                Nenhuma sessao disponivel ainda.
              </p>
            )}
          </div>
        </div>
      </div>

      <div className="border-t border-gray-100 p-3">
        <div className="mb-2 flex items-center gap-2 rounded-lg px-2 py-1.5">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-50 text-xs font-semibold text-primary-700">
            {(username || 'U').charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium text-gray-800">{username || 'Usuario'}</p>
            <p className="truncate text-xs text-gray-500">Conta e voz</p>
          </div>
          <NavLink
            to="/profile"
            onClick={onClose}
            className={({ isActive }) => [
              'flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-colors',
              isActive ? 'bg-primary-50 text-primary-700' : 'text-gray-500 hover:bg-gray-100 hover:text-gray-900',
            ].join(' ')}
            title="Perfil e voz"
          >
            <Settings className="h-4 w-4" />
          </NavLink>
        </div>
        <button
          type="button"
          onClick={onLogout}
          className="flex w-full min-h-[42px] items-center gap-3 rounded-lg px-3 text-sm font-medium text-gray-600 hover:bg-red-50 hover:text-red-600"
        >
          <LogOut className="h-4 w-4" />
          Sair
        </button>
      </div>
    </aside>
  );
};

const AuthenticatedShell = ({ username, selectedVoice, setSelectedVoice, onLogout }) => {
  const [userSessions, setUserSessions] = useState([]);
  const [userProgress, setUserProgress] = useState(null);
  const [loadingJourney, setLoadingJourney] = useState(true);
  const [journeyError, setJourneyError] = useState(null);
  const [startingSession, setStartingSession] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const refreshJourney = useCallback(async () => {
    if (!username) {
      setJourneyError('Username nao fornecido');
      setLoadingJourney(false);
      return;
    }

    try {
      setLoadingJourney(true);
      setJourneyError(null);
      const [sessionsResponse, progressResponse] = await Promise.all([
        getUserSessions(username),
        getUserProgress(username),
      ]);

      setUserSessions(sessionsResponse.data?.sessions || []);
      setUserProgress(progressResponse.data || null);
    } catch (error) {
      console.error('Erro ao carregar jornada:', error);
      setJourneyError('Erro ao carregar sessoes. ' + (error?.message || 'Tente novamente.'));
    } finally {
      setLoadingJourney(false);
    }
  }, [username]);

  useEffect(() => {
    refreshJourney();
  }, [refreshJourney]);

  useEffect(() => {
    if (!location.state?.message) {
      return;
    }

    setSuccessMessage(location.state.message);
    refreshJourney();
    navigate(location.pathname, { replace: true, state: {} });
  }, [location.pathname, location.state, navigate, refreshJourney]);

  useEffect(() => {
    if (!successMessage) {
      return undefined;
    }

    const timer = window.setTimeout(() => setSuccessMessage(null), 8000);
    return () => window.clearTimeout(timer);
  }, [successMessage]);

  const openSession = useCallback(async (session) => {
    if (!session || session.status === 'locked') {
      setJourneyError('Esta sessao ainda esta bloqueada. Complete as sessoes anteriores primeiro.');
      return;
    }

    try {
      setStartingSession(session.session_id);
      setJourneyError(null);

      let nextStatus = session.status;
      if (session.status === 'unlocked') {
        const startResult = await startUserSession(username, session.session_id);
        if (startResult.success) {
          nextStatus = 'in_progress';
          refreshJourney();
        }
      }

      const uniqueSessionId = `${username}_${session.session_id}`;
      setIsMobileMenuOpen(false);
      navigate(`/chat/${uniqueSessionId}`, {
        state: {
          username,
          sessionTitle: session.title,
          originalSessionId: session.session_id,
          userSession: {
            ...session,
            status: nextStatus,
          },
        },
      });
    } catch (error) {
      console.error('Erro ao abrir sessao:', error);
      setJourneyError('Erro ao iniciar sessao. Tente novamente.');
    } finally {
      setStartingSession(null);
    }
  }, [navigate, refreshJourney, username]);

  const clearJourneyError = useCallback(() => {
    setJourneyError(null);
  }, []);

  const outletContext = useMemo(() => ({
    username,
    selectedVoice,
    setSelectedVoice,
    userSessions,
    userProgress,
    loadingJourney,
    journeyError,
    startingSession,
    successMessage,
    clearJourneyError,
    openSession,
    refreshJourney,
    setSuccessMessage,
  }), [
    username,
    selectedVoice,
    setSelectedVoice,
    userSessions,
    userProgress,
    loadingJourney,
    journeyError,
    startingSession,
    successMessage,
    clearJourneyError,
    openSession,
    refreshJourney,
  ]);

  return (
    <div className="min-h-screen bg-background-light text-text-primary">
      <div className="hidden lg:fixed lg:inset-y-0 lg:left-0 lg:z-30 lg:block">
        <SidebarContent
          username={username}
          userSessions={userSessions}
          loadingJourney={loadingJourney}
          startingSession={startingSession}
          onClose={() => setIsMobileMenuOpen(false)}
          onLogout={onLogout}
          onOpenSession={openSession}
          onRefresh={refreshJourney}
        />
      </div>

      {isMobileMenuOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label="Fechar menu"
            className="absolute inset-0 h-full w-full bg-gray-950/40"
            onClick={() => setIsMobileMenuOpen(false)}
          />
          <div className="relative h-full w-72 max-w-[86vw]">
            <SidebarContent
              username={username}
              userSessions={userSessions}
              loadingJourney={loadingJourney}
              startingSession={startingSession}
              onClose={() => setIsMobileMenuOpen(false)}
              onLogout={onLogout}
              onOpenSession={openSession}
              onRefresh={refreshJourney}
            />
          </div>
        </div>
      )}

      <div className="flex min-h-screen flex-col lg:pl-72">
        <div className="sticky top-0 z-20 flex h-14 items-center justify-between border-b border-gray-200 bg-white/90 px-4 backdrop-blur-xl lg:hidden">
          <button
            type="button"
            onClick={() => setIsMobileMenuOpen(true)}
            className="flex h-10 w-10 items-center justify-center rounded-lg text-gray-600 hover:bg-gray-100"
            title="Abrir menu"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary-600" />
            <span className="font-heading text-sm font-semibold">Empat.IA</span>
          </div>
          <div className="h-10 w-10" />
        </div>

        <Outlet context={outletContext} />
      </div>
    </div>
  );
};

export default AuthenticatedShell;
