import React from 'react';
import { 
  Lock, 
  Unlock, 
  CheckCircle, 
  PlayCircle, 
  Clock,
  BookOpen,
  Target
} from 'lucide-react';

const SessionCard = ({ 
  session, 
  isUnlocked, 
  isCompleted, 
  isCurrent, 
  onSelect,
  index 
}) => {
  const getStatusIcon = () => {
    if (isCompleted) {
      return <CheckCircle className="w-6 h-6 text-emerald-500" />;
    }
    if (isCurrent) {
      return <PlayCircle className="w-6 h-6 text-orange-500" />;
    }
    if (isUnlocked) {
      return <Unlock className="w-6 h-6 text-primary-500" />;
    }
    return <Lock className="w-6 h-6 text-gray-400" />;
  };

  const getStatusText = () => {
    if (isCompleted) {
      return "Concluída";
    }
    if (isCurrent) {
      return "Em Andamento";
    }
    if (isUnlocked) {
      return "Disponível";
    }
    return "Bloqueada";
  };

  const getStatusColor = () => {
    if (isCompleted) {
      return "bg-emerald-50 border-emerald-200 text-emerald-700";
    }
    if (isCurrent) {
      return "bg-orange-50 border-orange-200 text-orange-700";
    }
    if (isUnlocked) {
      return "bg-primary-50 border-primary-200 text-primary-700";
    }
    return "bg-gray-50 border-gray-200 text-gray-500";
  };

  const getCardStyle = () => {
    if (isCompleted) {
      return "bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200 shadow-emerald-100";
    }
    if (isCurrent) {
      return "bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200 shadow-orange-100";
    }
    if (isUnlocked) {
      return "bg-gradient-to-br from-primary-50 to-primary-100 border-primary-200 shadow-primary-100 hover:shadow-primary-200";
    }
    return "bg-gradient-to-br from-gray-50 to-gray-100 border-gray-200 shadow-gray-100 opacity-60";
  };

  const canInteract = isUnlocked || isCurrent;

  return (
    <div
      className={`relative p-6 rounded-2xl border-2 transition-all duration-300 ${getCardStyle()} ${
        canInteract ? 'hover:shadow-lg cursor-pointer' : 'cursor-not-allowed'
      }`}
      onClick={() => canInteract && onSelect(session)}
    >
      {/* Número da sessão */}
      <div className="absolute -top-3 -left-3 w-8 h-8 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 text-white flex items-center justify-center font-bold text-sm shadow-lg">
        {index + 1}
      </div>

      {/* Status badge */}
      <div className={`absolute top-4 right-4 px-3 py-1 rounded-full text-xs font-medium border ${getStatusColor()}`}>
        <div className="flex items-center gap-1">
          {getStatusIcon()}
          {getStatusText()}
        </div>
      </div>

      {/* Conteúdo principal */}
      <div className="space-y-4">
        <div>
          <h3 className="font-heading text-lg text-text-primary dark:text-text-primary-dark font-semibold mb-2">
            {session.title}
          </h3>
          
          {session.subtitle && (
            <p className="text-sm text-text-secondary dark:text-text-secondary-dark mb-2">
              {session.subtitle}
            </p>
          )}
          
          {session.description && (
            <p className="text-sm text-text-secondary dark:text-text-secondary-dark reading-spacing">
              {session.description}
            </p>
          )}
        </div>

        {/* Informações da sessão */}
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span>{session.estimated_duration || 30} min</span>
          </div>
          
          {session.difficulty && (
            <div className="flex items-center gap-1">
              <Target className="w-3 h-3" />
              <span className="capitalize">{session.difficulty}</span>
            </div>
          )}
          
          {session.category && (
            <div className="flex items-center gap-1">
              <BookOpen className="w-3 h-3" />
              <span className="capitalize">{session.category}</span>
            </div>
          )}
        </div>

        {/* Botão de ação */}
        {canInteract && (
          <div className="pt-2">
            <button
              className={`w-full px-6 py-3 rounded-xl font-bold text-sm transition-all duration-200 flex items-center justify-center gap-2 shadow-md hover:shadow-lg text-white ${
                isCompleted ? 'bg-emerald-500 hover:bg-emerald-600' : 
                isCurrent ? 'bg-orange-500 hover:bg-orange-600' : 
                'bg-primary-500 hover:bg-primary-600'
              }`}
              style={{
                backgroundColor: isCompleted ? '#10b981' : isCurrent ? '#f59e0b' : '#4A90E2'
              }}
            >
              {isCompleted ? (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Revisar
                </>
              ) : isCurrent ? (
                <>
                  <PlayCircle className="w-4 h-4" />
                  Continuar
                </>
              ) : (
                <>
                  <Unlock className="w-4 h-4" />
                  Iniciar
                </>
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default SessionCard; 