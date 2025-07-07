import React from 'react';

const ProgressBar = ({ progress = 0, className = '' }) => {
  // Garantir que progress seja sempre um número entre 0 e 100
  let safeProgress = Number(progress);
  if (isNaN(safeProgress) || safeProgress < 0) safeProgress = 0;
  if (safeProgress > 100) safeProgress = 100;

  return (
    <div className={`w-full ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">Progresso Geral</span>
        <span className="text-sm font-medium text-gray-700">{safeProgress}%</span>
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div 
          className="bg-gradient-to-r from-blue-500 to-cyan-400 h-3 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${safeProgress}%` }}
        />
      </div>
      
      <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
        <span>Início da Jornada</span>
        <span>Mestre Terapêutico</span>
      </div>
    </div>
  );
};

export default ProgressBar; 