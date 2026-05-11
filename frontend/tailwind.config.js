export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "#0f1117",
          card: "#13151f",
          border: "#1e2133",
        },
        accent: {
          DEFAULT: "#2E75B6",
          light: "#3b82f6",
        },
        segment: {
          music:     "#22c55e",
          talk:      "#3b82f6",
          advert:    "#f59e0b",
          news:      "#8b5cf6",
          conflict:  "#ef4444",
          stationid: "#06b6d4",
          weather:   "#10b981",
          close:     "#6b7280",
        },
      },
    },
  },
  plugins: [],
};
