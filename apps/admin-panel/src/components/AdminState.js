import React from 'react';
import {
  ArrowPathIcon,
  ExclamationTriangleIcon,
  InboxIcon,
  SignalSlashIcon,
} from '@heroicons/react/24/outline';

export function LoadingState({ message = 'Carregando dados...' }) {
  return (
    <div className="flex items-center justify-center h-64 text-gray-600">
      <ArrowPathIcon className="w-5 h-5 animate-spin text-primary-600 mr-2" />
      <span>{message}</span>
    </div>
  );
}

export function ErrorState({ title = 'Erro ao carregar dados', message, onRetry }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
      <div className="flex">
        <ExclamationTriangleIcon className="h-5 w-5 text-red-500 flex-shrink-0" />
        <div className="ml-3">
          <h3 className="text-sm font-medium text-red-900">{title}</h3>
          <p className="mt-1 text-sm text-red-700">
            {message || 'O backend retornou uma falha para este contrato.'}
          </p>
          {onRetry && (
            <button
              type="button"
              onClick={onRetry}
              className="mt-3 text-sm font-medium text-red-700 hover:text-red-900"
            >
              Tentar novamente
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export function EmptyState({ title = 'Nenhum dado encontrado', message }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-gray-300 bg-white px-6 py-12 text-center">
      <InboxIcon className="h-10 w-10 text-gray-400" />
      <h3 className="mt-3 text-sm font-medium text-gray-900">{title}</h3>
      {message && <p className="mt-1 text-sm text-gray-500">{message}</p>}
    </div>
  );
}

export function UnavailableState({ title = 'Contrato ainda indisponível', message }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-yellow-200 bg-yellow-50 px-6 py-10 text-center">
      <SignalSlashIcon className="h-9 w-9 text-yellow-600" />
      <h3 className="mt-3 text-sm font-medium text-yellow-900">{title}</h3>
      <p className="mt-1 text-sm text-yellow-800">
        {message || 'A tela não recebeu dados reais para este bloco. Nenhum valor simulado foi exibido.'}
      </p>
    </div>
  );
}

export function DataQualityBadge({ unavailableFields = [] }) {
  if (!unavailableFields.length) {
    return (
      <span className="inline-flex items-center rounded-md bg-green-50 px-2 py-1 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20">
        Dados reais
      </span>
    );
  }

  return (
    <span className="inline-flex items-center rounded-md bg-yellow-50 px-2 py-1 text-xs font-medium text-yellow-800 ring-1 ring-inset ring-yellow-600/20">
      {unavailableFields.length} campo(s) indisponível(is)
    </span>
  );
}
