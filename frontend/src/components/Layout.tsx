import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  ShieldCheck,
  LayoutDashboard,
  FolderGit2,
  PlusCircle,
  LogOut,
  Menu,
  X,
  Code2,
  User as UserIcon,
} from 'lucide-react';

export const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  const navItems = [
    { name: 'Dashboard', to: '/dashboard', icon: LayoutDashboard },
    { name: 'Projects', to: '/projects', icon: FolderGit2 },
    { name: 'New Scan', to: '/projects/new', icon: PlusCircle },
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#e2e8f0] flex">
      {/* Mobile Menu Backdrop */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/70 backdrop-blur-sm z-40 lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar Navigation */}
      <aside
        className={`fixed top-0 bottom-0 left-0 z-50 w-64 bg-[#0d0d1a] border-r border-indigo-500/10 flex flex-col justify-between transition-transform duration-300 ease-in-out lg:translate-x-0 ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}
      >
        <div>
          {/* Logo Section */}
          <div className="h-18 px-6 py-5 flex items-center justify-between border-b border-indigo-500/10">
            <div
              className="flex items-center gap-3 cursor-pointer group"
              onClick={() => {
                navigate('/dashboard');
                setMobileMenuOpen(false);
              }}
            >
              <div className="p-2 rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 shadow-[0_0_16px_rgba(99,102,241,0.4)] group-hover:scale-105 transition-transform">
                <ShieldCheck className="w-6 h-6 text-white" />
              </div>
              <div>
                <span className="font-extrabold text-lg tracking-tight gradient-text block">
                  CodeReview AI
                </span>
                <span className="text-[10px] text-slate-500 uppercase tracking-widest font-mono">
                  Enterprise Security
                </span>
              </div>
            </div>

            <button
              onClick={() => setMobileMenuOpen(false)}
              className="lg:hidden text-slate-400 hover:text-white p-1"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Links */}
          <nav className="p-4 space-y-1.5 mt-2">
            <div className="px-3 pb-2 text-[11px] font-semibold tracking-wider text-slate-500 uppercase">
              Main Menu
            </div>
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setMobileMenuOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                      isActive
                        ? 'bg-gradient-to-r from-indigo-600/25 to-purple-600/15 text-indigo-300 border-l-4 border-indigo-500 shadow-[0_0_15px_rgba(99,102,241,0.25)] font-semibold'
                        : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                    }`
                  }
                >
                  <Icon className="w-5 h-5 shrink-0" />
                  <span>{item.name}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* User Info & Logout Footer */}
        <div className="p-4 border-t border-indigo-500/10 bg-[#0a0a14]/60">
          <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-900/60 border border-slate-800/80 mb-2">
            <div className="flex items-center gap-2.5 overflow-hidden">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center text-white font-bold text-sm shadow-md shrink-0">
                {user?.username ? user.username.charAt(0).toUpperCase() : <UserIcon className="w-4 h-4" />}
              </div>
              <div className="overflow-hidden">
                <p className="text-xs font-semibold text-slate-200 truncate">
                  {user?.username || 'User'}
                </p>
                <p className="text-[11px] text-slate-500 truncate" title={user?.email}>
                  {user?.email || 'user@example.com'}
                </p>
              </div>
            </div>
          </div>

          <button
            onClick={logout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium text-rose-400 hover:text-rose-300 hover:bg-rose-950/30 rounded-lg transition-colors border border-transparent hover:border-rose-900/40"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 lg:pl-64 flex flex-col min-h-screen">
        {/* Top Header bar for mobile toggle & ambient elements */}
        <header className="h-16 lg:hidden border-b border-indigo-500/10 px-4 flex items-center justify-between bg-[#0d0d1a]/80 backdrop-blur-md sticky top-0 z-30">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-lg bg-indigo-600/30 text-indigo-400">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <span className="font-bold text-base gradient-text">CodeReview AI</span>
          </div>

          <button
            onClick={() => setMobileMenuOpen(true)}
            className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <Menu className="w-6 h-6" />
          </button>
        </header>

        {/* Ambient Top Glow */}
        <div className="relative flex-1">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute top-20 right-10 w-80 h-80 bg-cyan-600/10 rounded-full blur-3xl pointer-events-none" />

          {/* Page outlet */}
          <main className="relative z-10 p-6 md:p-8 max-w-7xl mx-auto w-full">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
};

export default Layout;
