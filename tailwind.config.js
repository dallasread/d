/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom theme colors
        'theme-dark': {
          bg: '#1e1e1e',
          surface: '#252526',
          border: '#3e3e42',
          text: '#cccccc',
          'text-secondary': '#858585',
        },
        'theme-light': {
          bg: '#ffffff',
          surface: '#f3f3f3',
          border: '#e5e5e5',
          text: '#1e1e1e',
          'text-secondary': '#6e6e6e',
        },
        // Status colors
        success: '#4ade80',
        warning: '#fbbf24',
        error: '#ef4444',
      },
    },
  },
  plugins: [],
}
