import React, { useState, useEffect } from 'react';
import { Layers, Plus, LogOut, ShieldCheck, Sparkles, Trash2 } from 'lucide-react';
import { useAuth } from './hooks/useAuth';
import { Auth } from './components/Auth';
import { BusinessIdeaWizard } from './components/BusinessIdeaWizard';
import { DeliberationStream } from './components/DeliberationStream';
import { Dashboard } from './components/Dashboard';
import { api } from './lib/api';

export function App() {
  const { user, signIn, signOut } = useAuth();
  const [view, setView] = useState('wizard'); // 'wizard', 'deliberating', 'dashboard'
  const [activeProject, setActiveProject] = useState(null);
  const [reports, setReports] = useState([]);
  const [projectList, setProjectList] = useState([]);
  const [activeModel, setActiveModel] = useState('Gemma 4:12B');

  const loadProjects = async () => {
    try {
      const list = await api.listProjects();
      setProjectList(list);
    } catch (err) {
      console.error('Error fetching projects:', err);
    }
  };

  useEffect(() => {
    if (user) {
      loadProjects();
      api.getHealth().then((h) => {
        if (h?.ollama_model) {
          const formatted = h.ollama_model.includes('gemma') ? 'Gemma 4:12B' : h.ollama_model;
          setActiveModel(formatted);
        }
      }).catch(() => {});
    }
  }, [user]);

  const handleWizardComplete = (project) => {
    setActiveProject(project);
    setView('deliberating');
  };

  const handleDeliberationComplete = async () => {
    if (!activeProject) return;
    try {
      const data = await api.getReports(activeProject.id);
      setActiveProject(data.project);
      setReports(data.reports);
      setView('dashboard');
      loadProjects();
    } catch (err) {
      console.error('Failed to load completed reports:', err);
    }
  };

  const handleSelectProject = async (p) => {
    try {
      const data = await api.getReports(p.id);
      setActiveProject(data.project);
      setReports(data.reports);
      setView('dashboard');
    } catch (err) {
      console.error('Error loading project:', err);
    }
  };

  const handleDeleteProject = async (projectId, e) => {
    if (e) e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this venture blueprint and all its reports?')) {
      try {
        await api.deleteProject(projectId);
        if (activeProject && activeProject.id === projectId) {
          setActiveProject(null);
          setView('wizard');
        }
        await loadProjects();
      } catch (err) {
        alert('Failed to delete project: ' + err.message);
      }
    }
  };

  if (!user) {
    return <Auth onLogin={signIn} />;
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#080B11] text-slate-100 font-sans">
      {/* Top Navigation / Executive Bar */}
      <header className="border-b border-white/10 glass-panel sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-gradient-to-br from-gold-500/20 to-primary-600/20 border border-gold-500/30 rounded-xl text-gold-400 shadow-md shadow-gold-500/5">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-display font-bold text-sm tracking-tight text-white uppercase">Apex Venture Partners</span>
                <span className="text-[10px] font-mono text-gold-400 bg-gold-500/10 px-2 py-0.5 rounded-full border border-gold-500/30 font-semibold">
                  ADVISORY PRACTICE
                </span>
              </div>
              <p className="text-[11px] text-slate-400 hidden sm:block">Autonomous Executive Strategy, Sizing & Financial Modeling Studio</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden lg:flex items-center gap-2 text-xs text-slate-300 bg-white/5 px-3 py-1.5 rounded-xl border border-white/10">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              <span className="font-mono text-[11px]">Multi-Agent Chamber Active</span>
            </div>

            <div className="hidden md:flex items-center gap-2 text-xs text-emerald-400 bg-emerald-500/10 px-3 py-1.5 rounded-xl border border-emerald-500/20">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span className="font-semibold font-mono tracking-tight text-emerald-300">{activeModel}</span>
            </div>

            {view !== 'wizard' && (
              <button
                onClick={() => { setActiveProject(null); setView('wizard'); }}
                className="flex items-center gap-1.5 px-3.5 py-1.5 bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-500 hover:to-indigo-500 text-white rounded-xl text-xs font-semibold shadow-md shadow-primary-600/20 btn-press transition-all"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>New Engagement</span>
              </button>
            )}

            <button
              onClick={signOut}
              title="Sign Out"
              className="p-2 text-slate-400 hover:text-white rounded-xl hover:bg-white/5 btn-press transition-all"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Main Views */}
      <main className="flex-1">
        {view === 'wizard' && (
          <div>
            <BusinessIdeaWizard onComplete={handleWizardComplete} />
            {projectList.length > 0 && (
              <div className="max-w-4xl mx-auto px-4 pb-16">
                <div className="flex items-center justify-between border-b border-white/10 pb-3 mb-4">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-gold-400" />
                    <h3 className="text-xs uppercase font-bold text-slate-300 tracking-wider">
                      Archived Venture Strategy Memorandums
                    </h3>
                  </div>
                  <span className="text-[11px] text-slate-500 font-mono">{projectList.length} Engagements Stored</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
                  {projectList.map((p) => {
                    const score = p.overall_score || 0;
                    const ratingGrade = score >= 80 ? 'AAA - INVESTMENT READY' : score >= 65 ? 'AA - VIABLE' : 'GROWTH WEDGE';
                    return (
                      <div
                        key={p.id}
                        onClick={() => handleSelectProject(p)}
                        className="p-4 rounded-xl glass-panel hover:border-gold-500/40 cursor-pointer spring-hover transition-all border border-white/10 space-y-2 relative group"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-sm text-white group-hover:text-gold-300 transition-colors line-clamp-1">{p.name}</span>
                          <button
                            onClick={(e) => handleDeleteProject(p.id, e)}
                            title="Delete Memorandum"
                            className="p-1 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-lg transition-all opacity-0 group-hover:opacity-100"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>

                        <div className="flex items-center justify-between text-[10px]">
                          <span className="text-gold-400 font-mono font-bold bg-gold-500/10 px-2 py-0.5 rounded border border-gold-500/20">
                            {score ? `${score}/100 Score` : p.status}
                          </span>
                          <span className="text-slate-400 font-medium">{ratingGrade}</span>
                        </div>

                        <p className="text-xs text-slate-300 line-clamp-2 leading-relaxed">{p.problem_statement}</p>
                        
                        <div className="flex items-center justify-between text-[10px] text-slate-400 pt-2 border-t border-white/5">
                          <span>{p.industry}</span>
                          <span className="font-mono text-slate-500">{p.target_country}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}

        {view === 'deliberating' && activeProject && (
          <div className="max-w-4xl mx-auto py-12 px-4 space-y-6">
            <div className="text-center space-y-2">
              <h2 className="text-2xl font-bold text-white">Boardroom Deliberation in Progress</h2>
              <p className="text-xs text-slate-400 max-w-lg mx-auto">
                Specialized agents (Finance, Strategy, Marketing, Risk, Council, and Adversarial VC Critic) are formulating and stress-testing your venture plan.
              </p>
            </div>
            <DeliberationStream 
              projectId={activeProject.id} 
              onComplete={handleDeliberationComplete} 
              onRetry={() => api.generateReports(activeProject.id)}
            />
          </div>
        )}

        {view === 'dashboard' && activeProject && (
          <Dashboard
            project={activeProject}
            reports={reports}
            onBackToWizard={() => { setActiveProject(null); setView('wizard'); }}
            onRerun={() => { setView('deliberating'); api.generateReports(activeProject.id); }}
            onDelete={() => handleDeleteProject(activeProject.id)}
            onRefreshReports={async () => {
              try {
                const data = await api.getReports(activeProject.id);
                setReports(data.reports);
              } catch (e) {
                console.error('Failed to refresh reports:', e);
              }
            }}
          />
        )}
      </main>
    </div>
  );
}
export default App;
