import 'styled-components';

export interface Theme {
  colors: {
    background: string;
    surface: string;
    surfaceHover: string;
    border: string;
    text: string;
    textSecondary: string;
    textMuted: string;
    primary: string;
    primaryHover: string;
    success: string;
    error: string;
    warning: string;
    accent: string;
  };
  spacing: {
    xs: string;
    sm: string;
    md: string;
    lg: string;
    xl: string;
    xxl: string;
  };
  borderRadius: string;
  shadow: string;
  shadowHover: string;
}

declare module 'styled-components' {
  export interface DefaultTheme extends Theme {}
}

export const theme: Theme = {
  colors: {
    background: '#1a1a1a',
    surface: '#2d2d2d',
    surfaceHover: '#3a3a3a',
    border: '#404040',
    text: '#e0e0e0',
    textSecondary: '#b0b0b0',
    textMuted: '#808080',
    primary: '#4a4a4a',
    primaryHover: '#5a5a5a',
    success: '#4a5d4a',
    error: '#5d4a4a',
    warning: '#5d5a4a',
    accent: '#404040'
  },
  spacing: {
    xs: '4px',
    sm: '8px',
    md: '16px',
    lg: '24px',
    xl: '32px',
    xxl: '48px'
  },
  borderRadius: '8px',
  shadow: '0 4px 15px rgba(0,0,0,0.3)',
  shadowHover: '0 8px 25px rgba(0,0,0,0.4)'
}; 