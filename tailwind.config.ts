import type { Config } from "tailwindcss";
import animate from "tailwindcss-animate";

const config = {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#F8FAFC",
        surface: "#FFFFFF",
        primary: {
          DEFAULT: "#3B82F6",
          hover: "#2563EB"
        },
        success: "#22C55E",
        warning: "#F59E0B",
        danger: "#EF4444",
        border: "#E5E7EB",
        text: {
          primary: "#0F172A",
          secondary: "#64748B"
        },
        map: {
          highlight: "#60A5FA",
          glow: "rgba(96,165,250,.28)"
        }
      },
      borderRadius: {
        sm: "12px",
        md: "16px",
        lg: "20px",
        full: "999px"
      },
      spacing: {
        xs: "4px",
        sm: "8px",
        md: "16px",
        lg: "24px",
        xl: "32px"
      },
      boxShadow: {
        card: "0 8px 24px rgba(15,23,42,.06)",
        panel: "0 12px 32px rgba(15,23,42,.08)"
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"]
      },
      fontSize: {
        title: ["32px", { lineHeight: "1.15", fontWeight: "700" }],
        heading: ["24px", { lineHeight: "1.25", fontWeight: "600" }],
        body: ["16px", { lineHeight: "1.6", fontWeight: "400" }],
        caption: ["14px", { lineHeight: "1.45", fontWeight: "400" }]
      },
      transitionDuration: {
        fast: "150ms",
        normal: "250ms",
        slow: "400ms"
      },
      transitionTimingFunction: {
        smooth: "ease-out"
      },
      keyframes: {
        "panel-in": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" }
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" }
        }
      },
      animation: {
        "panel-in": "panel-in 250ms ease-out both",
        shimmer: "shimmer 1.5s ease-out infinite"
      }
    }
  },
  plugins: [animate]
} satisfies Config;

export default config;
