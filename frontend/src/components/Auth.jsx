import React, { useState } from 'react';
import { supabase } from '../lib/supabaseClient';
import { 
  Mail, 
  Lock, 
  User, 
  LogIn, 
  UserPlus, 
  AlertCircle,
  CheckCircle2,
  Layers,
  ArrowRight
} from 'lucide-react';

export default function Auth({ onAuthSuccess }) {
  const [isSignUp, setIsSignUp] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [errors, setErrors] = useState({});
  const [generalError, setGeneralError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [loading, setLoading] = useState(false);

  const validate = () => {
    const newErrors = {};
    if (!email.trim()) {
      newErrors.email = 'Email address is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = 'Email address is invalid';
    }

    if (!password) {
      newErrors.password = 'Password is required';
    } else if (password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
    }

    if (isSignUp && !fullName.trim()) {
      newErrors.fullName = 'Full Name is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleOAuthLogin = async (provider) => {
    setLoading(true);
    setGeneralError('');
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider,
        options: {
          redirectTo: window.location.origin
        }
      });
      if (error) throw error;
    } catch (err) {
      setGeneralError(err.message || 'OAuth authentication failed');
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setGeneralError('');
    setSuccessMsg('');
    if (!validate()) return;

    setLoading(true);
    try {
      if (isSignUp) {
        // Sign Up with Supabase
        const { data, error } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: {
              full_name: fullName
            }
          }
        });
        
        if (error) throw error;

        // Sync into public profiles
        if (data?.user) {
          const { error: profileError } = await supabase.from('profiles').upsert({
            id: data.user.id,
            email: data.user.email,
            full_name: fullName
          });
          if (profileError) {
            console.warn("Profiles syncing profile issue: ", profileError);
          }
        }

        setSuccessMsg('Registration successful! Please check your email inbox to confirm registration.');
        // Clean fields
        setFullName('');
        setEmail('');
        setPassword('');
      } else {
        // Sign In with Supabase
        const { data, error } = await supabase.auth.signInWithPassword({
          email,
          password
        });
        if (error) throw error;

        if (onAuthSuccess && data?.user) {
          onAuthSuccess(data.user);
        }
      }
    } catch (err) {
      setGeneralError(err.message || 'Authentication failed. Please verify your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 select-none relative overflow-hidden">
      {/* Background radial effects */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute -top-[10%] -left-[10%] w-[50%] h-[50%] bg-purple-500/10 rounded-full blur-[120px] animate-pulse-slow"></div>
        <div className="absolute -bottom-[10%] -right-[10%] w-[50%] h-[50%] bg-cyan-500/10 rounded-full blur-[120px] animate-pulse-slow"></div>
      </div>

      <div className="w-full max-w-md z-10">
        {/* Header Branding */}
        <div className="text-center mb-6 animate-float">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-purple-500/30 bg-purple-500/5 text-purple-300 text-xs font-semibold tracking-wider uppercase mb-3">
            <Layers className="w-3.5 h-3.5" />
            AI Venture Studio
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-cyan-400">
            Enterprise Portal
          </h1>
          <p className="text-gray-400 text-xs mt-1">
            Access startup modeling, intelligence pipelines, and boardroom debate systems.
          </p>
        </div>

        {/* Card */}
        <div className="glass rounded-2xl border border-white/5 shadow-2xl backdrop-blur-xl p-6 md:p-8">
          {/* Tabs */}
          <div className="flex border-b border-white/5 mb-6">
            <button
              onClick={() => {
                setIsSignUp(false);
                setErrors({});
                setGeneralError('');
                setSuccessMsg('');
              }}
              className={`flex-1 pb-3 text-sm font-semibold tracking-wide text-center border-b-2 transition-all ${
                !isSignUp
                  ? 'border-purple-500 text-purple-300 font-bold'
                  : 'border-transparent text-gray-500 hover:text-gray-400'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => {
                setIsSignUp(true);
                setErrors({});
                setGeneralError('');
                setSuccessMsg('');
              }}
              className={`flex-1 pb-3 text-sm font-semibold tracking-wide text-center border-b-2 transition-all ${
                isSignUp
                  ? 'border-purple-500 text-purple-300 font-bold'
                  : 'border-transparent text-gray-500 hover:text-gray-400'
              }`}
            >
              Register
            </button>
          </div>

          {/* Success / Error Boxes */}
          {generalError && (
            <div className="mb-5 p-3.5 rounded-lg border border-red-500/20 bg-red-500/5 text-red-400 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{generalError}</span>
            </div>
          )}

          {successMsg && (
            <div className="mb-5 p-3.5 rounded-lg border border-emerald-500/20 bg-emerald-500/5 text-emerald-400 text-xs flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 shrink-0 mt-0.5" />
              <span>{successMsg}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Full Name (Sign Up only) */}
            {isSignUp && (
              <div>
                <label className="block text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
                  Full Name
                </label>
                <div className="relative">
                  <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                    <User className="w-4.5 h-4.5" />
                  </span>
                  <input
                    type="text"
                    value={fullName}
                    onChange={(e) => {
                      setFullName(e.target.value);
                      if (errors.fullName) setErrors(prev => ({ ...prev, fullName: '' }));
                    }}
                    placeholder="Enter your name"
                    className={`w-full pl-10 pr-4 py-2.5 rounded-lg border bg-white/[0.02] text-sm text-white focus:outline-none transition-all placeholder:text-gray-600 ${
                      errors.fullName ? 'border-red-500/50 focus:border-red-500' : 'border-white/10 focus:border-purple-500'
                    }`}
                  />
                </div>
                {errors.fullName && (
                  <p className="mt-1 text-[10px] text-red-400 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" /> {errors.fullName}
                  </p>
                )}
              </div>
            )}

            {/* Email Address */}
            <div>
              <label className="block text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
                Email Address
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                  <Mail className="w-4.5 h-4.5" />
                </span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (errors.email) setErrors(prev => ({ ...prev, email: '' }));
                  }}
                  placeholder="name@company.com"
                  className={`w-full pl-10 pr-4 py-2.5 rounded-lg border bg-white/[0.02] text-sm text-white focus:outline-none transition-all placeholder:text-gray-600 ${
                    errors.email ? 'border-red-500/50 focus:border-red-500' : 'border-white/10 focus:border-purple-500'
                  }`}
                />
              </div>
              {errors.email && (
                <p className="mt-1 text-[10px] text-red-400 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {errors.email}
                </p>
              )}
            </div>

            {/* Password */}
            <div>
              <label className="block text-[10px] font-semibold text-gray-400 uppercase tracking-wider mb-1.5">
                Password
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3 flex items-center text-gray-500">
                  <Lock className="w-4.5 h-4.5" />
                </span>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    if (errors.password) setErrors(prev => ({ ...prev, password: '' }));
                  }}
                  placeholder="••••••••"
                  className={`w-full pl-10 pr-4 py-2.5 rounded-lg border bg-white/[0.02] text-sm text-white focus:outline-none transition-all placeholder:text-gray-600 ${
                    errors.password ? 'border-red-500/50 focus:border-red-500' : 'border-white/10 focus:border-purple-500'
                  }`}
                />
              </div>
              {errors.password && (
                <p className="mt-1 text-[10px] text-red-400 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> {errors.password}
                </p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-semibold text-white bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-600 hover:to-indigo-700 shadow-md transition-all mt-6"
            >
              {loading ? (
                <span className="w-4 h-4 rounded-full border-2 border-white/20 border-t-white animate-spin"></span>
              ) : isSignUp ? (
                <>
                  Create Account
                  <UserPlus className="w-4.5 h-4.5" />
                </>
              ) : (
                <>
                  Sign In
                  <LogIn className="w-4.5 h-4.5" />
                </>
              )}
            </button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/5"></div>
            </div>
            <div className="relative flex justify-center text-[10px] uppercase">
              <span className="bg-[#0b0816] px-2.5 text-gray-500 font-semibold tracking-wider">Or continue with</span>
            </div>
          </div>

          {/* Social Sign-In buttons */}
          <button
            type="button"
            disabled={loading}
            onClick={() => handleOAuthLogin('google')}
            className="w-full flex items-center justify-center gap-2.5 py-2.5 rounded-lg text-sm font-semibold text-white border border-white/10 hover:bg-white/5 transition-all"
          >
            {/* Custom Google SVG Icon */}
            <svg className="w-4.5 h-4.5" viewBox="0 0 24 24">
              <path
                fill="#EA4335"
                d="M12.24 10.285V14.4h6.887c-.648 2.41-2.519 4.114-5.136 4.114-3.478 0-6.3-2.822-6.3-6.3s2.822-6.3 6.3-6.3c1.606 0 3.058.607 4.17 1.6l3.057-3.057C19.348 2.724 16.037 1.7 12.24 1.7c-5.69 0-10.3 4.61-10.3 10.3s4.61 10.3 10.3 10.3c6.129 0 10.3-4.303 10.3-10.3 0-.688-.06-1.353-.172-1.715H12.24z"
              />
            </svg>
            Google Identity
          </button>
        </div>
      </div>
    </div>
  );
}
