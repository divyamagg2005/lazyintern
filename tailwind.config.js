/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        background: "#050816",
        surface: "#0b1020",
        accent: "#38bdf8",
        accentSoft: "#0f172a"
      }
    }
  },
  plugins: []
};

