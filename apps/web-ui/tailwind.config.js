/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    './index.html',
    './src/**/*.{js,jsx,ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Paleta de cores para saúde mental - Modo Claro
        primary: {
          50: '#EBF3FC',
          100: '#D7E7F9',
          200: '#AFCFF3',
          300: '#87B7ED',
          400: '#5F9FE7',
          500: '#4A90E2', // Azul Serenity - Primária
          600: '#3A7BC8',
          700: '#2A66AE',
          800: '#1A5194',
          900: '#0A3C7A',
        },
        secondary: {
          50: '#F0FBFE',
          100: '#E1F7FD',
          200: '#C3EFFB',
          300: '#A5E7F9',
          400: '#87DFF7',
          500: '#6ED2E8', // Turquesa Suave - Secundária
          600: '#5BB8D1',
          700: '#489EBA',
          800: '#3584A3',
          900: '#226A8C',
        },
        background: {
          light: '#F5F7FA', // Cinza Neutro - Fundo
          dark: '#1A2B4C', // Azul Escuro - Fundo Escuro
          card: '#FFFFFF',
          'card-dark': '#2E3B4E',
          muted: '#F8FAFC',
          'muted-dark': '#2A3B4E',
        },
        text: {
          primary: '#1A2B4C', // Azul Escuro - Texto Primário
          secondary: '#9FAAB5', // Cinza Médio - Texto Secundário
          muted: '#CBD5E1',
          'primary-dark': '#F1F5F9',
          'secondary-dark': '#CBD5E1',
          'muted-dark': '#64748B',
        },
        accent: {
          50: '#F5F3FF',
          100: '#EDE9FE',
          200: '#DDD6FE',
          300: '#C4B5FD',
          400: '#A78BFA',
          500: '#B28DFF', // Roxo Lavanda - Acento
          600: '#9333EA',
          700: '#7C3AED',
          800: '#6B21A8',
          900: '#581C87',
        },
        // Cores de estado para saúde mental
        success: {
          50: '#F0FDF4',
          100: '#DCFCE7',
          200: '#BBF7D0',
          300: '#86EFAC',
          400: '#4ADE80',
          500: '#22C55E',
          600: '#16A34A',
          700: '#15803D',
          800: '#166534',
          900: '#14532D',
        },
        warning: {
          50: '#FFFBEB',
          100: '#FEF3C7',
          200: '#FDE68A',
          300: '#FCD34D',
          400: '#FBBF24',
          500: '#F59E0B',
          600: '#D97706',
          700: '#B45309',
          800: '#92400E',
          900: '#78350F',
        },
        error: {
          50: '#FEF2F2',
          100: '#FEE2E2',
          200: '#FECACA',
          300: '#FCA5A5',
          400: '#F87171',
          500: '#EF4444',
          600: '#DC2626',
          700: '#B91C1C',
          800: '#991B1B',
          900: '#7F1D1D',
        },
        // Cores especiais para modo escuro
        dark: {
          background: '#1A2B4C',
          surface: '#2E3B4E',
          'surface-muted': '#2A3B4E',
          text: '#F1F5F9',
          'text-muted': '#CBD5E1',
          neon: '#4AD9D9', // Acento Neon
        },
        // Cores terapêuticas específicas
        therapy: {
          calm: '#4A90E2', // Azul Serenity
          hope: '#6ED2E8', // Turquesa Suave
          peace: '#B28DFF', // Roxo Lavanda
          growth: '#22C55E', // Verde Crescimento
          trust: '#4AD9D9', // Ciano Confiança
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        heading: ['Manrope', 'system-ui', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'xs': ['12px', { lineHeight: '16px' }],
        'sm': ['14px', { lineHeight: '20px' }], // Tamanho mínimo
        'base': ['16px', { lineHeight: '24px' }],
        'lg': ['18px', { lineHeight: '28px' }],
        'xl': ['20px', { lineHeight: '28px' }],
        '2xl': ['24px', { lineHeight: '32px' }],
        '3xl': ['30px', { lineHeight: '36px' }],
        '4xl': ['36px', { lineHeight: '40px' }],
        '5xl': ['48px', { lineHeight: '48px' }],
        '6xl': ['60px', { lineHeight: '60px' }],
      },
      backgroundImage: {
        'gradient-therapy': 'linear-gradient(135deg, #4A90E2 0%, #6ED2E8 50%, #B28DFF 100%)',
        'gradient-calm': 'linear-gradient(135deg, #4A90E2 0%, #6ED2E8 100%)',
        'gradient-hope': 'linear-gradient(135deg, #6ED2E8 0%, #B28DFF 100%)',
        'gradient-peace': 'linear-gradient(135deg, #B28DFF 0%, #4AD9D9 100%)',
        'glass-light': 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
        'glass-dark': 'linear-gradient(135deg, rgba(46,59,78,0.8) 0%, rgba(26,43,76,0.6) 100%)',
      },
      boxShadow: {
        'therapy-soft': '0 2px 4px -1px rgba(74, 144, 226, 0.1), 0 1px 2px -1px rgba(74, 144, 226, 0.06)',
        'therapy-medium': '0 4px 6px -1px rgba(74, 144, 226, 0.1), 0 2px 4px -1px rgba(74, 144, 226, 0.06)',
        'therapy-large': '0 10px 15px -3px rgba(74, 144, 226, 0.1), 0 4px 6px -2px rgba(74, 144, 226, 0.05)',
        'glow-primary': '0 0 20px rgba(74, 144, 226, 0.3)',
        'glow-secondary': '0 0 20px rgba(110, 210, 232, 0.3)',
        'glow-accent': '0 0 20px rgba(178, 141, 255, 0.3)',
        'glow-neon': '0 0 20px rgba(74, 217, 217, 0.4)',
      },
      borderRadius: {
        'xl': '1rem',
        '2xl': '1.5rem',
        '3xl': '2rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.6s ease-out',
        'slide-up': 'slideUp 0.8s ease-out',
        'pulse-soft': 'pulseSoft 2s ease-in-out infinite',
        'breathe': 'breathe 4s ease-in-out infinite',
        'float-gentle': 'floatGentle 6s ease-in-out infinite',
        'blink': 'blink 3s ease-in-out infinite',
        'glow': 'glow 2s ease-in-out infinite alternate',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseSoft: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
        breathe: {
          '0%, 100%': { transform: 'scale(1)' },
          '50%': { transform: 'scale(1.02)' },
        },
        floatGentle: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-8px)' },
        },
        blink: {
          '0%, 90%, 100%': { opacity: '1' },
          '95%': { opacity: '0.3' },
        },
        glow: {
          '0%': { boxShadow: '0 0 20px rgba(74, 144, 226, 0.3)' },
          '100%': { boxShadow: '0 0 30px rgba(74, 144, 226, 0.5)' },
        },
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
        '128': '32rem',
      },
      minHeight: {
        'screen-90': '90vh',
      },
      backdropBlur: {
        'xs': '2px',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('tailwindcss-animate'),
  ],
}; 