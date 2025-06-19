"""
Gmail OAuth Flow Module
======================
Handles OAuth2 authentication flow for Gmail API access.
"""

import os
from typing import Dict, Optional, Tuple, Any
import json
from datetime import datetime, timedelta

import requests
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

from config.settings import get_env_var
from utils.logging import get_logger

logger = get_logger(__name__)


class GmailOAuthFlow:
    """
    Handles the OAuth2 authentication flow for Gmail API access.
    
    This class manages:
    - OAuth2 authorization URL generation
    - Token exchange from authorization code
    - Token refresh when expired
    - User information retrieval
    - Token storage and revocation
    """
    
    # Default OAuth scopes for Gmail access
    DEFAULT_SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/userinfo.email',
        'https://www.googleapis.com/auth/userinfo.profile'
    ]
    
    def __init__(self, user_id: str = None):
        """
        Initialize Gmail OAuth flow.
        
        Args:
            user_id: ID of user for multi-tenant support
        """
        self.user_id = user_id
        self.client_id = get_env_var('GOOGLE_CLIENT_ID')
        self.client_secret = get_env_var('GOOGLE_CLIENT_SECRET')
        self.redirect_uri = get_env_var('GOOGLE_REDIRECT_URI')
        self.token_uri = 'https://oauth2.googleapis.com/token'
        self.auth_uri = 'https://accounts.google.com/o/oauth2/auth'
        self.scopes = self.DEFAULT_SCOPES
    
    def get_authorization_url(self, state: str = None, additional_scopes: list = None) -> str:
        """
        Generate authorization URL for OAuth2 flow.
        
        Args:
            state: Optional state parameter for CSRF protection
            additional_scopes: Additional OAuth scopes beyond defaults
            
        Returns:
            Authorization URL to redirect user to
        """
        # Create OAuth2 flow
        client_config = {
            "web": {
                "client_id": self.client_id,
                "client_secret": self.client_secret, 
                "auth_uri": self.auth_uri,
                "token_uri": self.token_uri,
                "redirect_uris": [self.redirect_uri]
            }
        }
        
        # Add any additional scopes
        scopes = list(self.scopes)  # Make a copy of default scopes
        if additional_scopes:
            scopes.extend(additional_scopes)
            
        try:
            # Create the flow using client secrets
            flow = Flow.from_client_config(
                client_config=client_config,
                scopes=scopes,
                redirect_uri=self.redirect_uri
            )
            
            # Generate the authorization URL
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent',
                state=state
            )
            
            logger.info(f"Generated authorization URL for user {self.user_id}")
            return auth_url
            
        except Exception as e:
            logger.error(f"Error generating auth URL: {str(e)}")
            raise
    
    def handle_oauth_callback(self, authorization_response: str) -> Dict[str, Any]:
        """
        Handle OAuth callback and exchange authorization code for access token.
        
        Args:
            authorization_response: Full callback URL with auth code
            
        Returns:
            Token info dictionary with access_token, refresh_token, etc.
        """
        try:
            # Create the flow
            client_config = {
                "web": {
                    "client_id": self.client_id,
                    "client_secret": self.client_secret, 
                    "auth_uri": self.auth_uri,
                    "token_uri": self.token_uri,
                    "redirect_uris": [self.redirect_uri]
                }
            }
            
            flow = Flow.from_client_config(
                client_config=client_config,
                scopes=self.scopes,
                redirect_uri=self.redirect_uri
            )
            
            # Exchange authorization code for tokens
            flow.fetch_token(authorization_response=authorization_response)
            
            # Get credentials
            credentials = flow.credentials
            
            # Create token info dictionary
            token_info = {
                'token_type': credentials.token_type,
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'id_token': getattr(credentials, 'id_token', None),
                'expires_at': datetime.utcnow().timestamp() + credentials.expiry.timestamp(),
                'scopes': credentials.scopes
            }
            
            logger.info(f"Successfully exchanged auth code for tokens for user {self.user_id}")
            return token_info
            
        except Exception as e:
            logger.error(f"Error handling OAuth callback: {str(e)}")
            raise
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        Refresh access token using refresh token.
        
        Args:
            refresh_token: The refresh token to use
            
        Returns:
            Updated token info or None if failed
        """
        try:
            credentials = Credentials(
                token=None,
                refresh_token=refresh_token,
                token_uri=self.token_uri,
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=self.scopes
            )
            
            # Try to refresh the token
            credentials.refresh(Request())
            
            # Create updated token info
            token_info = {
                'token_type': credentials.token_type,
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token or refresh_token,  # Use existing if not updated
                'expires_at': datetime.utcnow().timestamp() + credentials.expiry.timestamp(),
                'scopes': credentials.scopes
            }
            
            logger.info(f"Successfully refreshed tokens for user {self.user_id}")
            return token_info
            
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return None
    
    def get_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """
        Get Google user information using access token.
        
        Args:
            access_token: Valid access token
            
        Returns:
            User info dictionary or None if failed
        """
        try:
            # Call Google userinfo endpoint
            headers = {'Authorization': f'Bearer {access_token}'}
            response = requests.get(
                'https://www.googleapis.com/oauth2/v3/userinfo',
                headers=headers
            )
            
            response.raise_for_status()
            user_info = response.json()
            
            logger.info(f"Retrieved user info for user {self.user_id}")
            return user_info
            
        except Exception as e:
            logger.error(f"Error retrieving user info: {str(e)}")
            return None
    
    def is_token_valid(self, token_info: Dict[str, Any]) -> bool:
        """
        Check if access token is still valid.
        
        Args:
            token_info: Token info dictionary
            
        Returns:
            True if token is valid, False otherwise
        """
        # Check if we have an access token
        if not token_info.get('access_token'):
            return False
        
        # Check expiration time
        expires_at = token_info.get('expires_at')
        if not expires_at:
            return False
            
        # Add a buffer of 5 minutes to handle clock skew
        buffer_seconds = 300
        return datetime.utcnow().timestamp() < expires_at - buffer_seconds
    
    def revoke_token(self, token: str) -> bool:
        """
        Revoke a token (access or refresh token).
        
        Args:
            token: The token to revoke
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Call Google's revocation endpoint
            response = requests.post(
                'https://oauth2.googleapis.com/revoke',
                params={'token': token},
                headers={'content-type': 'application/x-www-form-urlencoded'}
            )
            
            # If status is 200, token was successfully revoked
            if response.status_code == 200:
                logger.info(f"Token successfully revoked for user {self.user_id}")
                return True
            else:
                logger.error(f"Error revoking token: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error revoking token: {str(e)}")
            return False
