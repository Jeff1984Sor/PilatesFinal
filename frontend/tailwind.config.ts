import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        canvas: "#f8f4ef",
        ink: "#1b1b1d",
        mint: "#c6f6d5",
        coral: "#ffb4a2",
        sky: "#a7c7ff",
        lemon: "#ffe066"
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui"],
        display: ["var(--font-display)", "ui-serif", "serif"]
      }
    }
  },
  plugins: []
};

export default config;
