/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Professional grayscale palette
        background: {
          primary: '#FFFFFF',
          secondary: '#FAFAFA',
        },
        text: {
          primary: '#1A1A1A',
          secondary: '#4A4A4A',
          tertiary: '#8A8A8A',
        },
        border: {
          DEFAULT: '#E5E5E5',
          light: '#F5F5F5',
        },
        // Minimal accent colors (use sparingly)
        brand: {
          DEFAULT: '#2563EB',
          hover: '#1D4ED8',
        },
        success: {
          DEFAULT: '#059669',
          light: '#F0FDF4',
          border: '#BBF7D0',
        },
        warning: {
          DEFAULT: '#D97706',
          light: '#FFFBEB',
          border: '#FDE68A',
        },
        error: {
          DEFAULT: '#DC2626',
          light: '#FEF2F2',
          border: '#FECACA',
          critical: '#991B1B',
        },
        beige: {
          50: '#FEFCF9',
          100: '#FDF8F0',
        },
      },
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Inter', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
      },
      fontSize: {
        'page-header': ['32px', { lineHeight: '1.2', fontWeight: '600', letterSpacing: '-0.5px' }],
        'section-header': ['24px', { lineHeight: '1.3', fontWeight: '600' }],
        'subsection-header': ['18px', { lineHeight: '1.4', fontWeight: '500' }],
        'body-large': ['16px', { lineHeight: '1.6', fontWeight: '400' }],
        'body-regular': ['14px', { lineHeight: '1.5', fontWeight: '400' }],
        'caption': ['13px', { lineHeight: '1.4', fontWeight: '400' }],
        'small': ['12px', { lineHeight: '1.4', fontWeight: '400' }],
      },
      spacing: {
        'screen-padding': '24px',
        'section': '32px',
        'element': '16px',
      },
      borderRadius: {
        'button': '6px',
        'input': '6px',
        'card': '8px',
      },
      boxShadow: {
        'card': '0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.1)',
        'card-hover': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
        'subtle': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
      },
    },
  },
  plugins: [],
}

