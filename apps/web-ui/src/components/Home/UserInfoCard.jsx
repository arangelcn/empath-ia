import React from 'react';
import { Card } from '../Common';

const UserInfoCard = ({ username, completedSessions = [], selectedVoice = {} }) => {
  return (
    <div className="fixed bottom-6 right-6 z-50">
      <Card variant="glass" className="p-5 border border-gray-200 dark:border-gray-700 min-w-[220px] max-w-xs animate-fade-in backdrop-blur-md">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 avatar-therapy-calm">
            <div className="w-full h-full bg-white rounded-full flex items-center justify-center">
              <svg className="w-4 h-4 text-primary-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
          </div>
          <span className="font-heading font-semibold text-text-primary dark:text-text-primary-dark text-lg">{username}</span>
        </div>
        
        {selectedVoice?.label && (
          <div className="flex items-center gap-2 mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
            <span className="text-lg">{selectedVoice.emoji}</span>
            <span className="text-sm text-accent-600 dark:text-accent-400 font-medium">{selectedVoice.label}</span>
          </div>
        )}
      </Card>
    </div>
  );
};

export default UserInfoCard; 