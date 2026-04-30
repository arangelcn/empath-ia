import React, { useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useOutletContext } from 'react-router-dom';
import {
  CheckCircle,
  Clock,
  Eye,
  Lock,
  PlayCircle,
  RefreshCw,
  Target,
  TrendingUp,
} from 'lucide-react';
import ProgressBar from './ProgressBar';

const statusStyles = {
  completed: {
    label: 'Concluida',
    icon: CheckCircle,
    badge: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    dot: 'bg-emerald-500',
    card: 'border-emerald-200 bg-emerald-50/70',
  },
  in_progress: {
    label: 'Em andamento',
    icon: Clock,
    badge: 'bg-amber-50 text-amber-700 border-amber-200',
    dot: 'bg-amber-500',
    card: 'border-amber-200 bg-amber-50/70',
  },
  unlocked: {
    label: 'Disponivel',
    icon: PlayCircle,
    badge: 'bg-blue-50 text-blue-700 border-blue-200',
    dot: 'bg-blue-500',
    card: 'border-blue-200 bg-blue-50/70',
  },
  locked: {
    label: 'Bloqueada',
    icon: Lock,
    badge: 'bg-gray-50 text-gray-500 border-gray-200',
    dot: 'bg-gray-300',
    card: 'border-gray-200 bg-gray-50',
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

const Metric = ({ label, value, tone = 'text-gray-900' }) => (
  <div className="rounded-lg border border-gray-200 bg-white px-4 py-3 text-center">
    <div className={`text-xl font-bold ${tone}`}>{value ?? 0}</div>
    <div className="mt-1 text-xs font-medium text-gray-500">{label}</div>
  </div>
);

const HomeScreen = () => {
  const {
    displayName,
    userSessions = [],
    userProgress,
    loadingJourney,
    journeyError,
    startingSession,
    successMessage,
    clearJourneyError,
    openSession,
    refreshJourney,
  } = useOutletContext();

  const sortedSessions = useMemo(() => (
    [...userSessions].sort((a, b) => getSessionRank(a) - getSessionRank(b) || String(a.title || '').localeCompare(String(b.title || '')))
  ), [userSessions]);

  useEffect(() => {
    if (!journeyError) {
      return undefined;
    }

    const timer = window.setTimeout(clearJourneyError, 5000);
    return () => window.clearTimeout(timer);
  }, [clearJourneyError, journeyError]);

  if (loadingJourney && userSessions.length === 0) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-background-light px-4">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center">
          <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-4 border-primary-100 border-t-primary-600" />
          <p className="text-sm font-medium text-gray-600">Carregando sua Home...</p>
        </motion.div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-background-light px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35 }}
          className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between"
        >
          <div>
            <p className="mb-2 text-xs font-semibold uppercase text-primary-600">Jornada continua</p>
            <h1 className="font-heading text-3xl font-bold text-gray-950">
              {displayName ? `Ola, ${displayName}` : 'Home'}
            </h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-gray-600">
              Continue de onde parou. Cada sessao preserva contexto, historico e progresso para a proxima conversa.
            </p>
          </div>

          <button
            type="button"
            onClick={refreshJourney}
            className="inline-flex min-h-[42px] items-center justify-center gap-2 rounded-lg border border-gray-200 bg-white px-4 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
          >
            <RefreshCw className={`h-4 w-4 ${loadingJourney ? 'animate-spin' : ''}`} />
            Atualizar
          </button>
        </motion.div>

        {successMessage && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm font-medium text-emerald-700"
          >
            {successMessage}
          </motion.div>
        )}

        {journeyError && (
          <motion.div
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-red-700"
          >
            {journeyError}
          </motion.div>
        )}

        {userProgress && (
          <section className="mb-6 rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
            <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-50 text-primary-700">
                  <TrendingUp className="h-5 w-5" />
                </div>
                <div>
                  <h2 className="text-lg font-semibold text-gray-950">Progresso</h2>
                  <p className="text-sm text-gray-500">Resumo da sua continuidade entre sessoes.</p>
                </div>
              </div>
              <div className="text-left sm:text-right">
                <div className="text-2xl font-bold text-primary-700">{userProgress.overall_progress}%</div>
                <div className="text-xs font-medium text-gray-500">geral</div>
              </div>
            </div>

            <ProgressBar progress={userProgress.overall_progress} className="mb-4" />

            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <Metric label="Concluidas" value={userProgress.completed_sessions} tone="text-emerald-600" />
              <Metric label="Em andamento" value={userProgress.in_progress_sessions} tone="text-amber-600" />
              <Metric label="Disponiveis" value={userProgress.unlocked_sessions} tone="text-blue-600" />
              <Metric label="Bloqueadas" value={userProgress.locked_sessions} tone="text-gray-500" />
            </div>
          </section>
        )}

        <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-sm">
          <div className="mb-5 flex items-start justify-between gap-4">
            <div>
              <h2 className="text-lg font-semibold text-gray-950">Sessoes da jornada</h2>
              <p className="mt-1 text-sm text-gray-500">
                Abra uma conversa existente ou avance para a proxima sessao disponivel.
              </p>
            </div>
          </div>

          <div className="relative">
            <div className="absolute bottom-0 left-4 top-0 hidden w-px bg-gray-200 sm:block" />

            <div className="space-y-3">
              {sortedSessions.map((session, index) => {
                const styles = statusStyles[session.status] || statusStyles.locked;
                const StatusIcon = styles.icon;
                const isInteractive = session.status !== 'locked';
                const isStarting = startingSession === session.session_id;

                return (
                  <motion.article
                    key={session.session_id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.25, delay: index * 0.04 }}
                    className="relative sm:pl-11"
                  >
                    <div className={`absolute left-1 top-5 hidden h-7 w-7 items-center justify-center rounded-full border-4 border-white ${styles.dot} sm:flex`}>
                      <StatusIcon className="h-3.5 w-3.5 text-white" />
                    </div>

                    <div className={`rounded-lg border p-4 transition-colors ${styles.card}`}>
                      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                        <div className="min-w-0 flex-1">
                          <div className="mb-2 flex flex-wrap items-center gap-2">
                            <h3 className="text-base font-semibold text-gray-950">
                              {session.title}
                            </h3>
                            <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 text-xs font-medium ${styles.badge}`}>
                              <StatusIcon className="h-3 w-3" />
                              {styles.label}
                            </span>
                          </div>

                          {session.subtitle && (
                            <p className="mb-1 text-sm font-medium text-gray-700">{session.subtitle}</p>
                          )}

                          {session.description && (
                            <p className="max-w-3xl text-sm leading-6 text-gray-600">{session.description}</p>
                          )}

                          <div className="mt-3 flex items-center gap-2 text-xs font-medium text-gray-500">
                            <Clock className="h-4 w-4" />
                            <span>{session.estimated_duration || '15-20 min'}</span>
                          </div>
                        </div>

                        <button
                          type="button"
                          onClick={() => openSession(session)}
                          disabled={!isInteractive || isStarting}
                          className={[
                            'inline-flex min-h-[42px] w-full shrink-0 items-center justify-center gap-2 rounded-lg px-4 text-sm font-semibold transition-colors md:w-auto',
                            session.status === 'completed'
                              ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                              : session.status === 'in_progress'
                                ? 'bg-amber-500 text-white hover:bg-amber-600'
                                : session.status === 'unlocked'
                                  ? 'bg-primary-600 text-white hover:bg-primary-700'
                                  : 'bg-gray-200 text-gray-500',
                            isStarting ? 'cursor-wait opacity-70' : '',
                          ].join(' ')}
                        >
                          {isStarting ? (
                            <>
                              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                              Abrindo...
                            </>
                          ) : session.status === 'completed' ? (
                            <>
                              <Eye className="h-4 w-4" />
                              Ver conversa
                            </>
                          ) : session.status === 'in_progress' ? (
                            'Continuar'
                          ) : session.status === 'unlocked' ? (
                            'Iniciar'
                          ) : (
                            'Bloqueada'
                          )}
                        </button>
                      </div>
                    </div>
                  </motion.article>
                );
              })}
            </div>

            {!loadingJourney && sortedSessions.length === 0 && (
              <div className="py-12 text-center">
                <Target className="mx-auto mb-4 h-12 w-12 text-gray-400" />
                <h3 className="mb-2 text-lg font-medium text-gray-950">Nenhuma sessao disponivel</h3>
                <p className="text-sm text-gray-500">As sessoes terapeuticas serao carregadas em breve.</p>
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
};

export default HomeScreen;
