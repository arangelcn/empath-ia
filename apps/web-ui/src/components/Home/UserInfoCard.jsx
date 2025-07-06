import React from 'react';
import { User } from 'lucide-react';

const UserInfoCard = ({ username, completedSessions = [], selectedVoice = {} }) => {
  return (
    <div className="fixed bottom-6 right-6 z-50">
      <div className="bg-white/90 backdrop-blur-md rounded-xl shadow-lg border border-gray-200 p-5 min-w-[220px] max-w-xs">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
            <User className="w-4 h-4 text-primary-600" />
          </div>
          <span className="font-semibold text-gray-900 text-lg">{username}</span>
        </div>
        
        <div className="text-sm text-gray-600 mb-3">
          {completedSessions.length} sessões concluídas
        </div>
        
        {selectedVoice?.label && (
          <div className="flex items-center gap-2 pt-3 border-t border-gray-200">
            <span className="text-lg">{selectedVoice.emoji || '🎤'}</span>
            <span className="text-sm text-primary-600 font-medium">{selectedVoice.label}</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default UserInfoCard; 