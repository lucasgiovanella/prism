/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./index.html', './src/**/*.{ts,tsx,js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: '#050816',
        surface: '#0f172a',
      },
      borderRadius: {
        xl: '1rem',
      },
      boxShadow: {
        glass: '0 10px 40px rgba(15,23,42,0.75)',
      },
      backdropBlur: {
        glass: '16px',
      },
    },
  },
  plugins: [],
};
