import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        forest: {
          50: "#f0f7f3",
          100: "#daeee2",
          200: "#b7ddc8",
          300: "#88c4a4",
          400: "#55a47b",
          500: "#33875b",
          600: "#236b46",
          700: "#1b5437",
          800: "#15432b",
          900: "#0f3020",
          950: "#081a11",
        },
        cream: {
          50: "#fefcf8",
          100: "#faf6ed",
          200: "#f4ecda",
          300: "#e9ddc5",
        },
      },
      fontFamily: {
        serif: ["var(--font-serif)", "Georgia", "serif"],
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
