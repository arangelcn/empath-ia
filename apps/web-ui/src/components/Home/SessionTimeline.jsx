import React from 'react';
import SessionItem from './SessionItem';

const SessionTimeline = ({ sessions, completedSessions, onAccess }) => {
  return (
    <div className="relative pl-6 animate-fade-in">
      <div className="absolute left-3 top-0 bottom-0 w-1 bg-gradient-to-b from-primary-300 via-secondary-300 to-accent-300 opacity-40 rounded-full" />
      <div className="space-y-3">
        {sessions.map((session, idx) => (
          <SessionItem
            key={session.id}
            id={session.id}
            title={session.title}
            description={session.description}
            completed={completedSessions.includes(session.id)}
            onAccess={onAccess}
          />
        ))}
      </div>
    </div>
  );
};

export default SessionTimeline; 