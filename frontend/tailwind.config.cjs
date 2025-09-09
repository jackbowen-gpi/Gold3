module.exports = {
  content: [
    '../../gchub_db/**/*.html',
    '../../gchub_db/**/*.py',
    './src/**/*.{js,jsx,ts,tsx,vue}'
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f5f8ff',
          100: '#e6f0ff',
          500: '#1f6feb',
          700: '#174bb5'
        }
      }
    }
  },
  plugins: []
}
