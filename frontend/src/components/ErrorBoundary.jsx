import React from 'react';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';

/**
 * ErrorBoundary — Catches unhandled React render errors and displays
 * a branded recovery screen instead of a white screen of death.
 */
export class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo });
    // Log to console for debugging (could be sent to a monitoring service)
    console.error('[ErrorBoundary] Caught error:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
  };

  handleGoHome = () => {
    this.setState({ hasError: false, error: null, errorInfo: null });
    // Force reload to clean state
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-[#080B11] text-slate-100 px-6">
          <div className="max-w-lg w-full text-center space-y-6">
            {/* Error Icon */}
            <div className="flex justify-center">
              <div className="p-4 bg-rose-500/15 border border-rose-500/30 rounded-2xl animate-pulse">
                <AlertTriangle className="w-10 h-10 text-rose-400" />
              </div>
            </div>

            {/* Heading */}
            <div className="space-y-2">
              <h1 className="text-2xl font-bold text-white font-display tracking-tight">
                Something went wrong
              </h1>
              <p className="text-sm text-slate-400 leading-relaxed max-w-md mx-auto">
                An unexpected error occurred in the application. Your data is safe — 
                you can retry the current action or return to the home screen.
              </p>
            </div>

            {/* Error Details (collapsible) */}
            {this.state.error && (
              <details className="text-left glass-panel rounded-xl border border-white/10 overflow-hidden">
                <summary className="px-4 py-3 text-xs font-semibold text-slate-300 cursor-pointer hover:bg-white/5 transition-colors flex items-center gap-2">
                  <Bug className="w-3.5 h-3.5 text-rose-400" />
                  <span>Technical Details</span>
                </summary>
                <div className="px-4 pb-4 space-y-2">
                  <pre className="text-[11px] font-mono text-rose-300 bg-slate-900/60 p-3 rounded-lg overflow-x-auto whitespace-pre-wrap border border-white/5">
                    {this.state.error.toString()}
                  </pre>
                  {this.state.errorInfo?.componentStack && (
                    <pre className="text-[10px] font-mono text-slate-500 bg-slate-900/40 p-3 rounded-lg overflow-x-auto whitespace-pre-wrap max-h-40 border border-white/5">
                      {this.state.errorInfo.componentStack}
                    </pre>
                  )}
                </div>
              </details>
            )}

            {/* Action Buttons */}
            <div className="flex items-center justify-center gap-3">
              <button
                onClick={this.handleReset}
                className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-primary-600 to-indigo-600 hover:from-primary-500 hover:to-indigo-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-primary-600/20 transition-all active:scale-95"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Try Again</span>
              </button>
              <button
                onClick={this.handleGoHome}
                className="flex items-center gap-2 px-5 py-2.5 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white rounded-xl text-sm font-medium border border-white/10 transition-all active:scale-95"
              >
                <Home className="w-4 h-4" />
                <span>Return Home</span>
              </button>
            </div>

            {/* Branding Footer */}
            <p className="text-[10px] text-slate-600 font-mono uppercase tracking-widest pt-4">
              Apex Venture Partners · Error Recovery System
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
