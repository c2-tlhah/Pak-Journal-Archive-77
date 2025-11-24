/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'neon-cyan': '#00f2ea',
        'neon-magenta': '#ff0050',
        'dark-gray': '#0f0f1a',
        'purple-dark': '#1a1625',
        'blue-dark': '#151b2e',
      },
      fontFamily: {
        'mono': ['Space Mono', 'JetBrains Mono', 'monospace'],
        'sans': ['Inter', 'system-ui', 'sans-serif'],
      },
      animation: {
        'glow-pulse': 'glow-pulse 2s ease-in-out infinite',
        'fade-in': 'fade-in 0.8s ease-out',
        'rotate-slow': 'rotate 60s linear infinite',
        'spin-slow': 'spin 20s linear infinite',
      },
      keyframes: {
        'glow-pulse': {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.5' },
        },
        'fade-in': {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        'rotate': {
          '0%': { transform: 'rotate(0deg)' },
          '100%': { transform: 'rotate(360deg)' },
        },
      },
      backgroundImage: {
        'dot-grid': 'radial-gradient(circle, rgba(255,255,255,0.05) 1px, transparent 1px)',
        'god-ray': 'radial-gradient(ellipse 120% 100% at 0% 0%, rgba(255,255,255,0.15) 0%, transparent 50%)',
      },
      backgroundSize: {
        'dot-grid': '30px 30px',
      },
    },
  },
  plugins: [],
}

