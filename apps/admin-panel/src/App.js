import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import './App.css';

import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './pages/Login';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';
import SystemStatus from './pages/SystemStatus';
import UserManagement from './pages/UserManagement';
import Analytics from './pages/Analytics';
import Conversations from './pages/Conversations';
import Settings from './pages/Settings';

function AuthenticatedApp() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/system-status" element={<SystemStatus />} />
        <Route path="/users" element={<UserManagement />} />
        <Route path="/analytics" element={<Analytics />} />
        <Route path="/conversations" element={<Conversations />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </Layout>
  );
}

function AppContent() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <Login />;
  }

  return <AuthenticatedApp />;
}

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <AppContent />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App; 