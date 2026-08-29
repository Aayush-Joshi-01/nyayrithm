import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class", '[data-theme="dark"]'],
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",

        /* The Night Court world — theme-aware via RGB channel variables */
        ink: {
          DEFAULT: "rgb(var(--ground) / <alpha-value>)",
          raised: "rgb(var(--raised) / <alpha-value>)",
          higher: "rgb(var(--higher) / <alpha-value>)",
        },
        bone: "rgb(var(--text) / <alpha-value>)",
        brass: {
          DEFAULT: "rgb(var(--brass) / <alpha-value>)",
          lit: "rgb(var(--brass-lit) / <alpha-value>)",
          text: "rgb(var(--brass-text) / <alpha-value>)",
        },
        oxblood: {
          DEFAULT: "rgb(var(--oxblood) / <alpha-value>)",
          bright: "rgb(var(--oxblood-bright) / <alpha-value>)",
        },
        ember: {
          DEFAULT: "rgb(var(--ember) / <alpha-value>)",
          text: "rgb(var(--ember-text) / <alpha-value>)",
        },
        role: {
          judge: "rgb(var(--role-judge) / <alpha-value>)",
          prosecutor: "rgb(var(--role-prosecutor) / <alpha-value>)",
          defense: "rgb(var(--role-defense) / <alpha-value>)",
          plaintiff: "rgb(var(--role-plaintiff) / <alpha-value>)",
          accused: "rgb(var(--role-accused) / <alpha-value>)",
          witness: "rgb(var(--role-witness) / <alpha-value>)",
          investigator: "rgb(var(--role-investigator) / <alpha-value>)",
          expert_witness: "rgb(var(--role-expert-witness) / <alpha-value>)",
          custom: "rgb(var(--role-custom) / <alpha-value>)",
        },
      },
      fontFamily: {
        sans: ["var(--font-franklin)", "ui-sans-serif", "system-ui", "sans-serif"],
        serif: ["var(--font-spectral)", "Iowan Old Style", "Georgia", "serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderRadius: {
        lg: "calc(var(--radius) + 3px)",
        md: "var(--radius)",
        sm: "calc(var(--radius) - 1px)",
      },
      letterSpacing: {
        caption: "0.34em",
      },
      boxShadow: {
        chamber: "var(--shadow-chamber)",
        "chamber-sm": "var(--shadow-chamber-sm)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(18px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        marquee: {
          "0%": { transform: "translateX(0)" },
          "100%": { transform: "translateX(-50%)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.6s cubic-bezier(0.16,1,0.3,1) forwards",
        marquee: "marquee 40s linear infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
