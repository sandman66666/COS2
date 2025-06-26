import React from 'react';
import styled from 'styled-components';

const AuthContainer = styled.div`
  display: flex;
  align-items: center;
  gap: ${props => props.theme.spacing.md};
  margin-bottom: ${props => props.theme.spacing.lg};
`;

const AuthButton = styled.a<{ isAuthenticated: boolean }>`
  display: inline-flex;
  align-items: center;
  gap: ${props => props.theme.spacing.sm};
  padding: ${props => props.theme.spacing.md} ${props => props.theme.spacing.lg};
  background: ${props => 
    props.isAuthenticated 
      ? props.theme.colors.success 
      : props.theme.colors.primary
  };
  color: ${props => props.theme.colors.text};
  text-decoration: none;
  border: 1px solid ${props => props.theme.colors.border};
  border-radius: ${props => props.theme.borderRadius};
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: ${props => props.theme.shadow};

  &:hover {
    background: ${props => 
      props.isAuthenticated 
        ? '#5a6d5a' 
        : props.theme.colors.primaryHover
    };
    box-shadow: ${props => props.theme.shadowHover};
    transform: translateY(-2px);
  }
`;

const AuthStatus = styled.span<{ isAuthenticated: boolean }>`
  color: ${props => 
    props.isAuthenticated 
      ? props.theme.colors.success 
      : props.theme.colors.textMuted
  };
  font-size: 0.9rem;
  font-weight: 500;
`;

const StatusIcon = styled.span<{ isAuthenticated: boolean }>`
  &:before {
    content: '${props => props.isAuthenticated ? '🔒' : '🔓'}';
    margin-right: ${props => props.theme.spacing.xs};
  }
`;

interface AuthButtonProps {
  isAuthenticated: boolean;
  onAuthChange: (authenticated: boolean) => void;
}

const AuthButtonComponent: React.FC<AuthButtonProps> = ({ isAuthenticated, onAuthChange }) => {
  const handleAuthClick = () => {
    if (isAuthenticated) {
      // For logout, we could implement a logout endpoint
      window.location.href = '/api/auth/logout';
    } else {
      // For login, redirect to Google OAuth
      window.location.href = '/api/auth/google';
    }
  };

  return (
    <AuthContainer>
      <AuthButton
        isAuthenticated={isAuthenticated}
        onClick={handleAuthClick}
        href="#"
      >
        <StatusIcon isAuthenticated={isAuthenticated} />
        {isAuthenticated ? 'Authenticated with Google' : 'Authenticate with Google'}
      </AuthButton>
      
      <AuthStatus isAuthenticated={isAuthenticated}>
        {isAuthenticated 
          ? '✅ Gmail access enabled' 
          : '⚠️ Authentication required for pipeline operations'
        }
      </AuthStatus>
    </AuthContainer>
  );
};

export default AuthButtonComponent; 