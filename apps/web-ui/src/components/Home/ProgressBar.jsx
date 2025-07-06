import React from 'react';

const ProgressBar = ({ progress = 0, className = '' }) => {
  return (
    <div className={`w-full ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">Progresso Geral</span>
        <span className="text-sm font-medium text-gray-700">{progress}%</span>
      </div>
      
      <div className="w-full bg-gray-200 rounded-full h-3">
        <div 
          className="bg-gradient-to-r from-primary-500 to-secondary-500 h-3 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${progress}%` }}
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