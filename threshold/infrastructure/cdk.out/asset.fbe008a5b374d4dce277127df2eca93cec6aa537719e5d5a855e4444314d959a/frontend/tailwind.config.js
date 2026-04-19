/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: "#0A1628",
        teal: "#0D7377",
        'teal-light': "#14BDAC",
        'red-alert': "#C0392B",
        orange: "#E67E22",
        yellow: "#F1C40F",
        'grey-dark': "#2C3E50",
        'grey-mid': "#BDC3C7",
        'grey-light': "#F4F6F8"
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      }
    },
  },
  plugins: [],
}
