/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        matPrimary: '#3f51b5',
        matPrimaryHover: '#303f9f',
        matBg: '#f5f5f5',
        matSurface: '#ffffff',
        matBorder: '#e0e0e0',
        matTextPrimary: 'rgba(0, 0, 0, 0.87)',
        matTextSecondary: 'rgba(0, 0, 0, 0.60)',
      },
      fontFamily: {
        sans: ['Roboto', 'Noto Sans TC', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
