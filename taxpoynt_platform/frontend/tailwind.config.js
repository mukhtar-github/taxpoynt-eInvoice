/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './design_system/**/*.{js,ts,jsx,tsx,mdx}',
    './shared_components/**/*.{js,ts,jsx,tsx,mdx}',
    './interfaces/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // TaxPoynt Brand Colors
        brand: {
          primary: '#0054B0',
          secondary: '#003875',
          accent: '#0066CC',
          light: '#E6F2FF',
        },
        
        // Nigerian Colors (for compliance/FIRS theming)
        nigeria: {
          green: '#008751',
          emerald: '#00A86B',
          forest: '#006341',
        },
        
        // Role-Based Colors
        roles: {
          si: '#0054B0',
          app: '#008751',
          hybrid: '#6366F1',
          admin: '#7C3AED',
        },
        
        // Custom semantic colors
        semantic: {
          success: '#10B981',
          warning: '#F59E0B',
          error: '#EF4444',
          info: '#3B82F6',
        }
      },
      
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
        display: ['Inter', 'system-ui', 'sans-serif'],
      },
      
      fontSize: {
        '2xs': '0.625rem',
      },
      
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    // Add any additional Tailwind plugins here
  ],
}