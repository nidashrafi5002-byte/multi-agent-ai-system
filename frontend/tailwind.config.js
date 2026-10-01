module.exports = {
  darkMode: ['class'],
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: '#0a0a0a',
        surface: '#111111',
        surfaceAlt: '#1a1a1a',
        border: '#1e1e1e',
        borderStrong: '#2a2a2a',
        textPrimary: '#eeeeee',
        textSecondary: '#888888',
        textMuted: '#555555',
        brand: '#3a6fff',
        brandGlow: '#64b5f6',
        success: '#4caf50',
        warning: '#FF6B35',
        danger: '#ef4444'
      },
      boxShadow: {
        panel: '0 0 0 1px rgba(255,255,255,0.04), 0 18px 40px rgba(0,0,0,0.28)',
        glow: '0 0 0 1px rgba(58,111,255,0.4), 0 22px 40px rgba(58,111,255,0.18)'
      },
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'sans-serif'],
        mono: ['SFMono-Regular', 'ui-monospace', 'monospace']
      },
      backgroundImage: {
        hero: 'linear-gradient(135deg, #0a0a2e 0%, #0d1b4b 50%, #1a1a3e 100%)'
      }
    }
  },
  plugins: [require('@tailwindcss/typography')]
};
