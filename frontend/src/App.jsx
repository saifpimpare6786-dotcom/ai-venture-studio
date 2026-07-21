import React, { useState } from 'react';
import { useAuth } from './hooks/useAuth';
import Auth from './components/Auth';
import BusinessIdeaWizard from './components/BusinessIdeaWizard';
import Dashboard from './components/Dashboard';
import { LogOut, User, Layers } from 'lucide-react';
import './App.css';

function App() {
  const { user, loading, signOut } = useAuth();
  const [currentProjectId, setCurrentProjectId] = useState(null);

  // Loading Splash Screen
  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#06040a] select-none">
        <div className="absolute inset-0 pointer-events-none overflow-hidden">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[300px] h-[300px] bg-purple-500/10 rounded-full blur-[80px]"></div>
        </div>
        <div className="relative flex flex-col items-center gap-4 z-10">
          <div className="w-12 h-12 rounded-xl border border-purple-500/30 bg-purple-500/5 flex items-center justify-center text-purple-400 shadow-[0_0_20px_rgba(168,85,247,0.2)] animate-pulse-slow">
            <Layers className="w-6 h-6 animate-spin" style={{ animationDuration: '3s' }} />
          </div>
          <div className="text-center">
            <h2 className="text-sm font-bold text-gray-300 uppercase tracking-widest">AI Venture Studio</h2>
            <p className="text-[10px] text-gray-500 mt-1 font-semibold">Loading Core Framework...</p>
          </div>
        </div>
      </div>
    );
  }

  // Not Authenticated -> Show Auth screen
  if (!user) {
    return (
      <div className="relative min-h-screen">
        <Auth />
      </div>
    );
  }

  // Authenticated -> Show main app gated behind auth
  return (
    <div className="relative min-h-screen flex flex-col">
      {/* Header bar */}
      <header className="z-20 w-full glass border-b border-white/5 py-4 px-6 md:px-12 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-purple-500/15 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <Layers className="w-4.5 h-4.5" />
          </div>
          <span className="font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-cyan-400 text-sm md:text-base">
            AI Venture Studio
          </span>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 text-xs text-gray-400 bg-white/[0.02] border border-white/5 rounded-full pl-2.5 pr-3.5 py-1">
            <User className="w-3.5 h-3.5 text-purple-400" />
            <span className="truncate max-w-[150px] font-medium">{user.email}</span>
          </div>

          <button
            onClick={signOut}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-white/10 hover:border-red-500/30 hover:bg-red-500/5 text-gray-400 hover:text-red-400 text-xs font-semibold transition-all cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            Sign Out
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="flex-1 flex flex-col justify-center relative">
        {currentProjectId ? (
          <Dashboard 
            projectId={currentProjectId} 
            onBackToWizard={() => setCurrentProjectId(null)} 
          />
        ) : (
          <BusinessIdeaWizard 
            onSubmitSuccess={(projectId) => setCurrentProjectId(projectId)} 
          />
        )}
      </main>
    </div>
  );
}

export default App;
