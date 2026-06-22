import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        sap: {
          blue: '#0070F2',
          'blue-dark': '#003D7A',
          'blue-light': '#E8F3FF',
          gold: '#F0AB00',
          green: '#107E3E',
          red: '#BB0000',
          gray: {
            100: '#F5F6F7',
            200: '#EDEFF0',
            300: '#D9DBDD',
            400: '#89919A',
            600: '#556B82',
            800: '#32363A',
          }
        }
      },
      fontFamily: {
        sans: ['72', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
export default config
