/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'olympic-blue': '#0081C8',
        'olympic-red': '#EE334E',
        'olympic-gold': '#FCB131',
        'surveillance-warning': '#FF6B6B',
        'data-safe': '#4ECDC4',
      }
    },
  },
  plugins: [],
}
