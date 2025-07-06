import React from 'react';
import { CheckCircle, Clock } from 'lucide-react';

const SessionItem = ({ id, title, description, completed, onAccess }) => {
  return (
    <div className="flex items-start gap-4 relative group py-4">
      <div className="flex flex-col items-center">
        {completed ? (
          <div className="w-6 h-6 bg-green-100 rounded-full flex items-center justify-center">
            <CheckCircle className="w-4 h-4 text-green-600" />
          </div>
        ) : (
          <div className="w-6 h-6 bg-primary-100 rounded-full flex items-center justify-center group-hover:bg-primary-200 transition-colors duration-200">
            <Clock className="w-4 h-4 text-primary-600" />
          </div>
        )}
        <div className="w-1 flex-1 bg-gradient-to-b from-primary-200 via-secondary-200 to-primary-200 opacity-40 mt-2" />
      </div>
      
      <div className="flex-1 bg-white rounded-xl shadow-sm border border-gray-100 hover:shadow-md transition-all duration-200 group-hover:border-primary-200">
        <div className="p-4">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {title}
          </h3>
          
          {description && (
            <p className="text-sm text-gray-600 mb-4">
              {description}
            </p>
          )}
          
          <button
            onClick={() => onAccess(id)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 transition-colors duration-200 text-sm font-medium"
          >
            <span>Acessar Sessão</span>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default SessionItem; 