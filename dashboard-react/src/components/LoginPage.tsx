import React from 'react';
import styled from 'styled-components';

const LoginContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, ${props => props.theme.colors.background} 0%, ${props => props.theme.colors.surface} 100%);
  padding: ${props => props.theme.spacing.lg};
`;

const LoginCard = styled.div`
  background: ${props => props.theme.colors.surface};
  padding: ${props => props.theme.spacing.xxl};
  border-radius: ${props => props.theme.borderRadius};
  box-shadow: ${props => props.theme.shadowHover};
  border: 1px solid ${props => props.theme.colors.border};
  text-align: center;
  max-width: 400px;
  width: 100%;
`;

const Logo = styled.div`
  font-size: 3rem;
  margin-bottom: ${props => props.theme.spacing.lg};
  color: ${props => props.theme.colors.primary};
`;

const Title = styled.h1`
  font-size: 2rem;
  font-weight: 300;
  margin-bottom: ${props => props.theme.spacing.md};
  color: ${props => props.theme.colors.text};
`;

const Subtitle = styled.p`
  color: ${props => props.theme.colors.textMuted};
  margin-bottom: ${props => props.theme.spacing.xl};
  line-height: 1.6;
`;

const LoginButton = styled.button`
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: ${props => props.theme.spacing.md};
  padding: ${props => props.theme.spacing.lg} ${props => props.theme.spacing.xl};
  background: ${props => props.theme.colors.primary};
  color: ${props => props.theme.colors.text};
  border: none;
  border-radius: ${props => props.theme.borderRadius};
  font-size: 1.1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  width: 100%;
  box-shadow: ${props => props.theme.shadow};

  &:hover {
    background: ${props => props.theme.colors.primaryHover};
    box-shadow: ${props => props.theme.shadowHover};
    transform: translateY(-2px);
  }

  svg {
    width: 20px;
    height: 20px;
  }
`;

const GoogleIcon = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
  </svg>
);

const SecurityNote = styled.div`
  margin-top: ${props => props.theme.spacing.lg};
  padding: ${props => props.theme.spacing.md};
  background: ${props => props.theme.colors.background};
  border-radius: ${props => props.theme.borderRadius};
  font-size: 0.9rem;
  color: ${props => props.theme.colors.textMuted};
`;

interface LoginPageProps {
  onLogin?: () => void;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin }) => {
  const handleGoogleLogin = () => {
    console.log('🔑 Login button clicked - starting Google OAuth...');
    
    try {
      // Detect environment and construct proper OAuth URL
      const isLocalhost = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
      
      let redirectUrl;
      if (isLocalhost) {
        // Local development: use explicit port 8080
        redirectUrl = `${window.location.protocol}//${window.location.hostname}:8080/auth/google`;
      } else {
        // Production (Heroku): use same domain without port
        redirectUrl = `${window.location.protocol}//${window.location.host}/auth/google`;
      }
      
      console.log('🔗 Environment detected:', isLocalhost ? 'localhost' : 'production');
      console.log('🔗 Redirecting to:', redirectUrl);
      
      // Direct redirect to backend OAuth endpoint
      window.location.href = redirectUrl;
    } catch (error) {
      console.error('❌ Login redirect failed:', error);
      // Fallback: try relative path
      window.location.href = '/auth/google';
    }
  };

  return (
    <LoginContainer>
      <LoginCard>
        <Logo>🧠</Logo>
        <Title>Strategic Intelligence System</Title>
        <Subtitle>
          CEO-Grade Personal AI Intelligence Platform
          <br />
          Sign in to access your intelligence dashboard
        </Subtitle>
        
        <LoginButton onClick={handleGoogleLogin}>
          <GoogleIcon />
          Sign in with Google
        </LoginButton>
        
        <SecurityNote>
          🔒 Your data is encrypted and secure. We only access your Gmail to extract business intelligence insights.
        </SecurityNote>
      </LoginCard>
    </LoginContainer>
  );
};

export default LoginPage; 