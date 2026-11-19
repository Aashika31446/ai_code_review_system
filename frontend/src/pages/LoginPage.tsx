import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { ShieldCheck, Mail, Lock, Eye, EyeOff, ArrowRight, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';

export const LoginPage: React.FC = () => {
  const [emailOrUsername, setEmailOrUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emailOrUsername.trim() || !password) {
      toast.error('Please enter your credentials');
      return;
    }

    try {
      setIsSubmitting(true);
      // Support both email or username in the request
      const isEmail = emailOrUsername.includes('@');
      await login({
        email: isEmail ? emailOrUsername : undefined,
        username: !isEmail ? emailOrUsername : emailOrUsername,
        password,
      });
    } catch (error) {
      // Handled in auth context
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Background radial glow decorations */}
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-indigo-600/15 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] bg-purple-600/15 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[350px] h-[350px] bg-cyan-600/10 rounded-full blur-[90px] pointer-events-none" />

      {/* Grid Pattern Overlay */}
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage:
            'radial-gradient(circle at 1px 1px, #ffffff 1px, transparent 0)',
          backgroundSize: '32px 32px',
        }}
      />

      {/* Centered Glass Card */}
      <div className="relative z-10 w-full max-w-md animate-in fade-in zoom-in-95 duration-500">
        <div className="glass-card rounded-2xl p-8 sm:p-10 border border-indigo-500/20 backdrop-blur-2xl">
          {/* Logo & Header */}
          <div className="flex flex-col items-center text-center mb-8">
            <div className="relative mb-3">
              <div className="absolute inset-0 bg-indigo-500/30 rounded-2xl blur-lg" />
              <div className="relative p-3.5 rounded-2xl bg-gradient-to-tr from-indigo-600 to-purple-600 shadow-xl border border-indigo-400/30">
                <ShieldCheck className="w-8 h-8 text-white" />
              </div>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight gradient-text">
              CodeReview AI
            </h1>
            <p className="text-xs text-slate-400 mt-1 max-w-xs">
              AI-assisted static code analysis & automated vulnerability remediation
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Email or Username
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  required
                  value={emailOrUsername}
                  onChange={(e) => setEmailOrUsername(e.target.value)}
                  placeholder="developer@example.com"
                  className="w-full glass-input text-sm rounded-xl pl-10 pr-4 py-3 text-slate-100 placeholder-slate-500"
                />
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider">
                  Password
                </label>
                <span className="text-[11px] text-indigo-400 hover:text-indigo-300 cursor-pointer">
                  Forgot?
                </span>
              </div>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type={showPassword ? 'text' : 'password'}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full glass-input text-sm rounded-xl pl-10 pr-11 py-3 text-slate-100 placeholder-slate-500"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full btn-primary py-3 px-4 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 group cursor-pointer disabled:opacity-60 transition-all"
            >
              {isSubmitting ? (
                <>
                  <Sparkles className="w-4 h-4 animate-spin text-white" />
                  <span>Signing In...</span>
                </>
              ) : (
                <>
                  <span>Sign In to Workspace</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          {/* Footer link to Register */}
          <div className="mt-8 pt-6 border-t border-slate-800/80 text-center">
            <p className="text-xs text-slate-400">
              Don't have an account yet?{' '}
              <Link
                to="/register"
                className="text-indigo-400 hover:text-indigo-300 font-semibold ml-1 transition-colors underline-offset-4 hover:underline"
              >
                Create account
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
