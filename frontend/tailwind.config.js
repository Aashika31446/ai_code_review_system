/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#0a0a0f',
        surface: '#12121a',
        card: '#1a1a2e',
        'card-hover': '#242442',
        border: 'rgba(99, 102, 241, 0.15)',
        primary: {
          DEFAULT: '#6366f1',
          hover: '#4f46e5',
          light: '#818cf8',
        },
        secondary: {
          DEFAULT: '#8b5cf6',
          hover: '#7c3aed',
          light: '#a78bfa',
        },
        accent: {
          DEFAULT: '#06b6d4',
          hover: '#0891b2',
          light: '#22d3ee',
        },
        success: '#10b981',
        warning: '#f59e0b',
        error: '#ef4444',
        critical: '#dc2626',
        text: {
          DEFAULT: '#e2e8f0',
          muted: '#94a3b8',
          dark: '#64748b',
        },
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        glow: {
          '0%': { boxShadow: '0 0 5px rgba(99, 102, 241, 0.4), 0 0 20px rgba(99, 102, 241, 0.2)' },
          '100%': { boxShadow: '0 0 15px rgba(99, 102, 241, 0.7), 0 0 30px rgba(139, 92, 246, 0.4)' },
        },
      },
    },
  },
  plugins: [],
}
