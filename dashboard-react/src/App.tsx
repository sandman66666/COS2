import React, { useState, useEffect } from 'react';
import styled, { createGlobalStyle, ThemeProvider } from 'styled-components';
import axios from 'axios';
import { theme } from './theme';
import Dashboard from './components/Dashboard';
import LoginPage from './components/LoginPage';

const GlobalStyle = createGlobalStyle`
  * {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    background: ${props => props.theme.colors.background};
    color: ${props => props.theme.colors.text};
    line-height: 1.6;
  }

  button {
    font-family: inherit;
    cursor: pointer;
    border: none;
    outline: none;
    transition: all 0.3s ease;
  }

  input, textarea {
    font-family: inherit;
    outline: none;
  }

  pre {
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  }

  ::-webkit-scrollbar {
    width: 8px;
  }

  ::-webkit-scrollbar-track {
    background: ${props => props.theme.colors.surface};
  }

  ::-webkit-scrollbar-thumb {
    background: ${props => props.theme.colors.border};
    border-radius: 4px;
  }

  ::-webkit-scrollbar-thumb:hover {
    background: ${props => props.theme.colors.primary};
  }
`;

const AppContainer = styled.div`
  min-height: 100vh;
  background: ${props => props.theme.colors.background};
`;

const LoadingContainer = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: ${props => props.theme.colors.background};
`;

const LoadingSpinner = styled.div`
  width: 40px;
  height: 40px;
  border: 3px solid ${props => props.theme.colors.border};
  border-top: 3px solid ${props => props.theme.colors.primary};
  border-radius: 50%;
  animation: spin 1s linear infinite;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null); // null = loading
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    checkAuthentication();
    handleUrlParams();
  }, []);

  const handleUrlParams = () => {
    const urlParams = new URLSearchParams(window.location.search);
    
    if (urlParams.get('login_success')) {
      console.log('🎉 Login successful - redirected from OAuth');
      // Clean up URL parameters
      window.history.replaceState({}, '', '/');
    }
    
    if (urlParams.get('logged_out')) {
      console.log('👋 Logged out successfully');
      setIsAuthenticated(false);
      // Clean up URL parameters
      window.history.replaceState({}, '', '/');
    }
    
    if (urlParams.get('force_logout')) {
      console.log('🔄 Force logout completed');
      setIsAuthenticated(false);
      // Clean up URL parameters
      window.history.replaceState({}, '', '/');
    }
  };

  const checkAuthentication = async () => {
    try {
      const response = await axios.get('/api/auth/status');
      setIsAuthenticated(response.data.authenticated);
    } catch (error) {
      console.error('Auth check failed:', error);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAuthChange = (authenticated: boolean) => {
    setIsAuthenticated(authenticated);
  };

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <ThemeProvider theme={theme}>
        <GlobalStyle />
        <LoadingContainer>
          <LoadingSpinner />
        </LoadingContainer>
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={theme}>
      <GlobalStyle />
      <AppContainer>
        {isAuthenticated ? (
          <Dashboard onAuthChange={handleAuthChange} />
        ) : (
          <LoginPage onLogin={() => checkAuthentication()} />
        )}
      </AppContainer>
    </ThemeProvider>
  );
}

export default App;
