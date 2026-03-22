/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        vibe: {
          bg: '#080810',
          surface: '#0f0f1a',
          card: '#13131f',
          border: '#1e1e30',
          muted: '#2a2a3e',
          purple: '#7c3aed',
          'purple-light': '#9f67ff',
          pink: '#ec4899',
          'pink-light': '#f472b6',
          cyan: '#06b6d4',
          text: '#f0f0f8',
          'text-muted': '#9090a8',
          'text-dim': '#5a5a72',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp: { from: { opacity: '0', transform: 'translateY(12px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
      },
      backgroundImage: {
        'gradient-vibe': 'linear-gradient(135deg, #080810 0%, #0f0822 50%, #080810 100%)',
        'gradient-card': 'linear-gradient(180deg, #16162a 0%, #13131f 100%)',
        'glow-purple': 'radial-gradient(ellipse at center, rgba(124,58,237,0.15) 0%, transparent 70%)',
        'glow-pink': 'radial-gradient(ellipse at center, rgba(236,72,153,0.12) 0%, transparent 70%)',
      },
    },
  },
  plugins: [],
}
