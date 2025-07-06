import React from 'react';
import { Button, Card } from '../Common';

const SessionItem = ({ id, title, description, completed, onAccess }) => {
  return (
    <div className="flex items-start gap-4 relative group py-4">
      <div className="flex flex-col items-center">
        {completed ? (
          <div className="w-6 h-6 bg-success-100 dark:bg-success-900/30 rounded-full flex items-center justify-center">
            <svg className="w-3 h-3 text-success-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          </div>
        ) : (
          <div className="w-6 h-6 bg-accent-100 dark:bg-accent-900/30 rounded-full flex items-center justify-center group-hover:bg-primary-100 dark:group-hover:bg-primary-900/30 transition-colors duration-200">
            <div className="w-2 h-2 bg-accent-600 dark:bg-accent-400 rounded-full group-hover:bg-primary-600 dark:group-hover:bg-primary-400 transition-colors duration-200" />
          </div>
        )}
        <div className="w-1 flex-1 bg-gradient-to-b from-primary-200 via-secondary-200 to-accent-200 opacity-40" />
      </div>
      
      <Card variant="glass" hover className="flex-1">
        <div className="p-4">
          <h3 className="font-heading text-lg text-text-primary dark:text-text-primary-dark font-semibold mb-2">
            {title}
          </h3>
          
          {description && (
            <p className="text-sm text-text-secondary dark:text-text-secondary-dark mb-4 reading-spacing">
              {description}
            </p>
          )}
          
          <Button
            variant="primary"
            size="sm"
            onClick={() => onAccess(id)}
            className="flex items-center gap-2"
            aria-label={`Acessar ${title}`}
          >
            <span>Acessar Sessão</span>
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Button>
        </div>
      </Card>
    </div>
  );
};

export default SessionItem; 