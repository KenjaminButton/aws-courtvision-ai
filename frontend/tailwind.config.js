/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'iowa': {
          gold: '#FFCD00',
          black: '#000000',
          'gold-dark': '#E5B800',
          'gold-light': '#FFE066',
        },
        'court': {
          wood: '#CD853F',
          'wood-dark': '#8B5A2B',
          line: '#FFFFFF',
          key: '#FFCD00',
        }
      },
      fontFamily: {
        'display': ['Impact', 'Haettenschweiler', 'Arial Narrow Bold', 'sans-serif'],
        'body': ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
        'mono': ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      backgroundImage: {
        'diagonal-stripes': 'repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(255,205,0,0.05) 10px, rgba(255,205,0,0.05) 20px)',
        'court-texture': 'linear-gradient(90deg, #CD853F 0%, #8B5A2B 50%, #CD853F 100%)',
      },
      animation: {
        'pulse-gold': 'pulse-gold 2s ease-in-out infinite',
        'slide-up': 'slide-up 0.3s ease-out',
        'fade-in': 'fade-in 0.5s ease-out',
        'score-pop': 'score-pop 0.3s ease-out',
      },
      keyframes: {
        'pulse-gold': {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(255, 205, 0, 0.4)' },
          '50%': { boxShadow: '0 0 0 10px rgba(255, 205, 0, 0)' },
        },
        'slide-up': {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'score-pop': {
          '0%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.2)' },
          '100%': { transform: 'scale(1)' },
        },
      },
    },
  },
  plugins: [],
}
