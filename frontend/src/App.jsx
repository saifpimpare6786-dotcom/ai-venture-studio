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
      <div className="min-h-screen flex flex-col items-center justify-center bg-[#F8F9FB] select-none">
        <div className="relative flex flex-col items-center gap-4 z-10">
          <div className="w-12 h-12 rounded-xl border border-[#5B4CE0]/20 bg-[#5B4CE0]/10 flex items-center justify-center text-[#5B4CE0] shadow-sm animate-pulse-slow">
            <Layers className="w-6 h-6 animate-spin" style={{ animationDuration: '3s' }} />
          </div>
          <div className="text-center">
            <h2 className="text-xs font-bold text-[#1A1D23] uppercase tracking-widest">AI Venture Studio</h2>
            <p className="text-[11px] text-[#98A2B3] mt-1 font-medium">Loading Intelligence Framework...</p>
          </div>
        </div>
      </div>
    );
  }

  // Not Authenticated -> Show Auth screen
  if (!user) {
    return (
      <div className="relative min-h-screen bg-[#F8F9FB]">
        <Auth />
      </div>
    );
  }

  // Authenticated -> Show main app gated behind auth
  return (
    <div className="relative min-h-screen flex flex-col bg-[#F8F9FB]">
      {/* Header bar */}
      <header className="z-20 w-full bg-white border-b border-[#E4E7EC] py-3.5 px-6 md:px-12 flex items-center justify-between shadow-xs">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-[#5B4CE0] flex items-center justify-center text-white shadow-xs">
            <Layers className="w-4.5 h-4.5" />
          </div>
          <div className="flex flex-col">
            <span className="font-bold tracking-tight text-[#1A1D23] text-base leading-none">
              AI Venture Studio
            </span>
            <span className="text-[10px] font-semibold text-[#98A2B3] uppercase tracking-wider mt-0.5">
              Investment & Strategy Platform
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 text-xs text-[#4B5565] bg-[#F8F9FB] border border-[#E4E7EC] rounded-full pl-2.5 pr-3.5 py-1">
            <User className="w-3.5 h-3.5 text-[#5B4CE0]" />
            <span className="truncate max-w-[160px] font-medium">{user.email}</span>
          </div>

          <button
            onClick={signOut}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-[#E4E7EC] hover:border-red-200 hover:bg-red-50 text-[#4B5565] hover:text-red-600 text-xs font-semibold transition-all cursor-pointer"
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
